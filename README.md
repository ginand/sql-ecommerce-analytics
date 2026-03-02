# 📊 SQL E-commerce Analytics (PostgreSQL Portfolio Project)

End-to-end Data Analytics project using PostgreSQL and Python.

This project simulates a realistic e-commerce database and performs:

- Revenue & Profitability Analysis
- Channel Performance Analysis
- Category Profit & Margin Analysis
- Returns Risk Assessment
- RFM Customer Segmentation
- Cohort Retention Analysis

---

# 🛠 Tech Stack

- PostgreSQL
- Python (pandas, numpy, psycopg)
- SQL (CTE, Window Functions, Aggregation, Cohort logic)

---

# 📂 Project Structure


sql-ecommerce-analytics/
│
├── sql/
│ └── 00_schema.sql
│
├── scripts/
│ ├── generate_data.py
│ └── load_postgres.py
│
├── queries/
│ ├── 01_create_views.sql
│ ├── 02_kpi_monthly.sql
│ ├── 03_channel_performance.sql
│ ├── 04_category_profit.sql
│ ├── 05_top_products.sql
│ ├── 06_returns_analysis.sql
│ ├── 07_rfm_segmentation.sql
│ ├── 08_cohort_retention.sql
│ └── 09_data_quality_checks.sql
│
└── insights/
└── insights.md


---

# 🚀 Setup Guide

## 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
2️⃣ Set DATABASE_URL

PowerShell:

$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/da_portfolio"

3️⃣ Generate Data
python scripts/generate_data.py
4️⃣ Load into PostgreSQL
python scripts/load_postgres.py
📈 Key Results

Total Net Revenue: 15,028,154.66

Total Gross Profit: 3,512,106.70

Overall Return Rate: 5.88%

Electronics Revenue Share: 13.48%

Electronics Margin: 23.40%

Month-1 Retention: 45.75%

🧠 Business Insights

See detailed findings in:

insights/insights.md

🎯 Project Highlights

✔ Realistic data generation
✔ Proper schema design (constraints, enums, indexes)
✔ Net revenue modeling (payments - refunds)
✔ Profitability analysis
✔ RFM segmentation
✔ Cohort retention

👤 Author

TAN DAT
Data Analytics Intern Candidate


---
