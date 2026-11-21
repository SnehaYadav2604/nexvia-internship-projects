DROP TABLE IF EXISTS balance_sheet, gl_budget_actual, accounts CASCADE;

CREATE TABLE accounts (
    account_id    INT PRIMARY KEY,
    account_name  TEXT,
    account_type  TEXT,
    base_budget   NUMERIC
);

CREATE TABLE gl_budget_actual (
    month       DATE,
    account_id  INT REFERENCES accounts(account_id),
    budget      NUMERIC,
    actual      NUMERIC
);

CREATE TABLE balance_sheet (
    month      DATE,
    line_item  TEXT,
    section    TEXT,
    amount     NUMERIC
);

