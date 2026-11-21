import os
import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/finance_risk")
CSV = "data/german_credit.csv"

if os.path.exists(CSV):
    df = pd.read_csv(CSV)
else:
    df = fetch_openml("credit-g", version=1, as_frame=True).frame
    df.to_csv(CSV, index=False)

df["good"] = (df["class"] == "good").astype(int)
df = df.drop(columns=["class"])
df.insert(0, "applicant_id", range(1, len(df) + 1))
features = [c for c in df.columns if c not in ("applicant_id", "good")]
train, test = train_test_split(df, test_size=0.3, stratify=df["good"], random_state=42)

def make_bins(s, edges):
    return pd.cut(s, edges).astype(str) if edges is not None else s.astype(str)

# ---- weight of evidence and information value (training data only) ----
edges_map, woe_maps, iv_rows, woe_rows = {}, {}, [], []
for f in features:
    edges = None
    if pd.api.types.is_numeric_dtype(train[f]):
        edges = np.unique(np.quantile(train[f], [0, .2, .4, .6, .8, 1.0])).astype(float)
        edges[0], edges[-1] = -np.inf, np.inf
        edges_map[f] = edges
    t = pd.DataFrame({"bin": make_bins(train[f], edges), "good": train["good"]})
    g = t.groupby("bin")["good"].agg(["count", "sum"])
    g.columns = ["n", "good"]
    g["bad"] = g["n"] - g["good"]
    gd = g["good"].clip(lower=0.5)
    bd = g["bad"].clip(lower=0.5)
    g["woe"] = np.log((gd / gd.sum()) / (bd / bd.sum()))
    g["iv"] = ((gd / gd.sum()) - (bd / bd.sum())) * g["woe"]
    woe_maps[f] = g["woe"].to_dict()
    iv_rows.append((f, g["iv"].sum()))
    for k, r in g.iterrows():
        woe_rows.append((f, str(k), int(r["n"]), round(float(r["woe"]), 4), round(float(r["iv"]), 4)))

iv = pd.DataFrame(iv_rows, columns=["feature", "iv"]).sort_values("iv", ascending=False)
selected = iv[iv["iv"] >= 0.05]["feature"].tolist()

def to_woe(d):
    out = pd.DataFrame(index=d.index)
    for f in selected:
        out[f] = make_bins(d[f], edges_map.get(f)).map(woe_maps[f]).fillna(0.0)
    return out

Xtr, Xte = to_woe(train), to_woe(test)
model = LogisticRegression(max_iter=1000).fit(Xtr, train["good"])

def ks(y, p):
    d = pd.DataFrame({"y": y.values, "p": p}).sort_values("p")
    cum_good = (d["y"] == 1).cumsum() / (d["y"] == 1).sum()
    cum_bad = (d["y"] == 0).cumsum() / (d["y"] == 0).sum()
    return float((cum_bad - cum_good).abs().max())

auc_train = roc_auc_score(train["good"], model.predict_proba(Xtr)[:, 1])
auc_test = roc_auc_score(test["good"], model.predict_proba(Xte)[:, 1])
ks_test = ks(test["good"], model.predict_proba(Xte)[:, 1])

# ---- score scaling: 600 points = 50:1 good:bad odds, +20 points doubles the odds ----
FACTOR = 20 / np.log(2)
OFFSET = 600 - FACTOR * np.log(50)

allX = to_woe(df)
df["score"] = (OFFSET + FACTOR * model.decision_function(allX)).round(0)
df["pd_bad"] = (1 - model.predict_proba(allX)[:, 1]).round(4)
df["risk_band"] = pd.qcut(df["score"].rank(method="first"), 5, labels=["E", "D", "C", "B", "A"]).astype(str)
df["split"] = np.where(df["applicant_id"].isin(test["applicant_id"]), "test", "train")
df["is_bad"] = 1 - df["good"]

summary = (df.groupby("risk_band")
             .agg(applicants=("applicant_id", "count"),
                  bad_rate_pct=("is_bad", lambda s: round(100 * s.mean(), 1)),
                  avg_score=("score", "mean"), min_score=("score", "min"), max_score=("score", "max"))
             .reset_index().sort_values("risk_band"))
summary["avg_score"] = summary["avg_score"].round(0)

df[["applicant_id", "score", "pd_bad", "risk_band", "split", "is_bad"]].to_sql(
    "credit_scores", engine, if_exists="replace", index=False)
summary.to_sql("credit_band_summary", engine, if_exists="replace", index=False)
pd.DataFrame(woe_rows, columns=["feature", "bin", "applicants", "woe", "iv"]).to_sql(
    "woe_iv", engine, if_exists="replace", index=False)

text = (f"German Credit scorecard (1000 applicants, 70/30 train/test split)\n"
        f"Selected features (IV >= 0.05): {', '.join(selected)}\n"
        f"AUC train: {auc_train:.3f} | AUC test: {auc_test:.3f} | KS test: {ks_test:.3f}\n"
        f"Scaling: 600 points at 50:1 good:bad odds, 20 points to double the odds\n\n"
        f"{summary.to_string(index=False)}\n")
print(text)
open("docs/scorecard_metrics.txt", "w").write(text)

