## Files
| File | Purpose |
|---|---|
| `scripts/00_extract_data.py` | Auto-unzip → DuckDB load → rebuild `job_categories` |
| `scripts/03_eda_report.py` | First-look EDA printed to console |
| `scripts/01_clean_data.py` | 16 group cleaning rules + feature engineering (logs every drop) |
| `scripts/02_build_duckdb.py` | Verify tables + schema |
| `notebooks/01_data_cleaning.ipynb` | Cleaning walkthrough (Pandas) |
| `notebooks/02_eda.ipynb` | 7 dashboard metrics, Matplotlib/Seaborn |
| `app.py` | Streamlit dashboard (Plotly) — **16 charts across 4 tabs** |

## Technique → where → why (Module 1 lessons)

| Lesson | Applied in | Why |
|---|---|---|
| **1.1 Intro Data Science** | This README + PRESENTATION.md | Frame the business question before code |
| **1.2 Intro Database** | DuckDB file `data/sg_jobs.duckdb` | File-based analytical DB, no server |
| **1.3 SQL DDL** | `00_extract_data.py` CREATE TABLE | Define `raw_jobs`, `job_categories` |
| **1.4 SQL DML** | `COPY`, `SELECT`, `DESCRIBE` | Load/export and sanity-check |
| **1.5 SQL Advanced** | `unnest` + `json_extract_string` on `categories` | Normalise JSON array to one row per (job, category) |
| **1.6 NumPy** | Percentile line, heatmap, histogram thresholds in `app.py` (metric 6) | EP benchmarks are percentiles — NumPy `percentile` gives p33/p50/p65/p90 directly |
| **1.7 Pandas** | `01_clean_data.py` + every `groupby` behind the 16 charts | Vectorised, reproducible transforms |
| **1.8 EDA basic** | KPI row, ranked bar, treemap (Overview tab) | Show totals, shares and outliers before drilling in |
| **1.9 EDA advanced** | Mismatch index, open-days boxplot, repost bars, time trend | The business question ("hard to fill?") is a derived metric |
| **1.10 Visualisation** | **16 charts** in `app.py`: ranked bar · scatter (×2) · treemap · stacked bar · diverging bar · boxplot · percentile line · grouped bar · histogram (×2) · heatmap · time line; Matplotlib/Seaborn versions in notebooks | One chart per *decision*; colour-blind-safe palette; `Insight:` captions written for non-technical stakeholders |

## Visual inventory (what each chart is for)
| # | Tab | Chart | Decision it supports |
|---|---|---|---|
| 1 | Overview | KPI row (4 × `st.metric`) | At-a-glance totals |
| 2 | Overview | Ranked bar — top categories by applications | Which categories are hot |
| 3 | Overview | Scatter — vacancies vs mean salary | Are big-need categories also high-paid? |
| 4 | Overview | Treemap — application share | Share-of-whole across categories |
| 5 | Overview | Stacked bar — PMET vs Non-PMET share | Which categories EP policy most affects |
| 6 | Hiring Health | Bar (reds) — avg open days | Hard-to-fill roles |
| 7 | Hiring Health | Bar (oranges) — avg reposts | Chronic bottlenecks |
| 8 | Hiring Health | Diverging bar — mismatch index | Shortage vs healthy |
| 9 | Hiring Health | Boxplot — open-days spread | Real delay vs outliers |
| 10 | Hiring Health | Bubble scatter — vacancy/apps (size=salary) | Shortage quadrant |
| 11 | Wage | Percentile line + EP/S Pass hlines | Policy alignment |
| 12 | Wage | Grouped bar — PMET vs Non-PMET median | The PMET premium |
| 13 | Wage | Histogram + threshold lines | Share clearing each bar |
| 14 | Wage | Heatmap — category × percentile | Compare all categories at once |
| 15 | Drill-down | Histogram — salary (filtered) | Shape of the slice |
| 16 | Drill-down | Time line — first posted vs reposted | Market re-post pressure |