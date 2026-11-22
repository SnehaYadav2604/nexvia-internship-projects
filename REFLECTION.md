# Individual Reflection: Sneha Yadav

## What I built and what I owned
I completed both assigned projects end to end on my own MacBook. DA-03 is a supply chain control tower: an hourly data feed into PostgreSQL, KPIs in SQL, z-score anomaly detection, a Prophet demand forecast compared with current stock, Slack alerts, an Airflow hourly pipeline, and a Superset dashboard with a what-if view (supplier delayed by 7 days). DA-04 is a finance and risk system: a synthetic company ledger, P&L, budget-vs-actual and balance sheet views in SQL, a credit risk scorecard (weight of evidence and logistic regression) with risk bands, a monthly PDF board pack, an Airflow monthly pipeline, and a Superset dashboard. I wrote automated tests for both (10 and 8 tests, all passing) and documented the architecture, KPI definitions and setup in each README.

## The hardest parts
My Mac is an older Intel MacBook on macOS 13, so Docker was not an option. I had to install PostgreSQL, Airflow and Superset directly, each in its own virtual environment because their package versions conflicted. Several setup errors took time to work through: a Python SSL certificate error that blocked Slack alerts, Superset failing to start because of a missing package and a version mismatch in a caching library, and a port that was already in use. I also could not get the Superset dashboard filter working, so I replaced it with a fixed 7-day what-if table plus a line chart that shows every delay from 0 to 14 days. Power Pivot, Qlik Sense and Power Automate were not available on macOS, so I used SQL, Superset and Airflow instead and said so in the README.

## What I learned
- How a data pipeline fits together: data, database, checks, forecast, alerts and dashboard, with Airflow scheduling the steps.
- Anomaly detection with z-scores, and why the alert threshold matters (normal noise scored 3 to 4, real spikes scored above 7).
- That Prophet beat a simple 14-day average baseline (14.7% vs 17.9% WAPE) but not by a huge margin on simple data.
- How to define KPIs clearly (stock-out rate, on-time delivery, days of inventory) so the numbers can be trusted.
- How a credit scorecard works: weight of evidence, information value, score scaling, risk bands, and how to judge it with AUC (0.762 on test data) and KS (0.448). I also noticed the gap between train and test AUC, which suggests mild overfitting.
- Practical habits: reading error messages, committing often, writing tests, and keeping secrets like the Slack webhook out of the repository.

## What I would do next
- Connect real data feeds and deploy the system to the cloud instead of running it locally.
- Email the monthly board pack automatically, and rebuild the Excel, Qlik Sense and Power Automate parts on a Windows machine.
- Validate the scorecard on a separate out-of-time sample and add the dashboard filter for the what-if panel.
- Keep studying the code I ran, so I can explain and change every part of it myself.