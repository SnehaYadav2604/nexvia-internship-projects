# Metric definitions (DA-04)

| Metric | Definition |
|---|---|
| Revenue | Sum of actual amounts of all Revenue accounts (4010 to 4040) in the month |
| COGS | Sum of actual amounts of Cost of Goods Sold accounts (5010, 5020) |
| Gross profit | Revenue minus COGS |
| Opex | Sum of actual amounts of operating expense accounts (6010 to 6060) |
| Net income | Revenue minus COGS minus Opex (before tax and interest) |
| Budget net income | The same calculation using budget amounts |
| Variance | Actual minus budget, summed over the last 3 months for each account |
| Variance % | Variance divided by budget, times 100 |
| Favorable / Unfavorable | Revenue above budget or costs below budget is favorable; the opposite is unfavorable |
| Balance sheet identity | Assets = Liabilities + Equity, checked for every month |
| Weight of evidence (WoE) | ln(share of good applicants in a bin / share of bad applicants in the bin) |
| Information value (IV) | Sum over bins of (share good minus share bad) times WoE. Features with IV of at least 0.05 are used |
| Credit score | 600 points at 50:1 good:bad odds; every 20 points doubles the odds |
| Probability of default (pd_bad) | 1 minus the model's probability of a good loan |
| Risk band | Applicants split into 5 equal groups by score: A (best) to E (worst) |
| Default rate | Share of applicants in a band whose loan was bad |
| AUC | Probability that a random good applicant scores higher than a random bad one (0.5 = random, 1.0 = perfect) |
| KS | Maximum gap between the cumulative good and bad score distributions |
