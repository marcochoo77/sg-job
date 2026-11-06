
---

# 11. `LEARNING_NOTES.md`

```markdown
# Learning Notes — how each lesson technique maps to this project

> Not displayed in the Streamlit app — this is your personal study guide.

## 1.1 — Intro Data Science
**Where:** README + PRESENTATION.md
**Why:** A data product starts with a decision to support. Here: MOM Policy Officers need
a data-driven view of the market before adjusting Work-Pass thresholds.

## 1.2 — Intro Database
**Where:** DuckDB file `data/sg_jobs.duckdb`
**Why:** Analytical workloads (`GROUP BY`, `unnest`, `json_extract`) are simpler on a
columnar file DB. No server to install; the file *is* the DB.

## 1.3 — SQL DDL
**Where:** `00_extract_data.py` — `CREATE TABLE raw_jobs`, `CREATE TABLE job_categories`
**Why:** Schema-first thinking forces you to name and type the data before transforming.

## 1.4 — SQL DML
**Where:** `COPY raw_jobs TO ...`, `DESCRIBE clean_jobs`
**Why:** Populating and querying tables is the way you *verify* your pipeline at every step.

## 1.5 — SQL Advanced (JSON normalisation)
**Where:** your exact `unnest` + `json_extract_string` snippet
**Why:** `categories` is a JSON array. Keeping it as a string forces string hacks;
`unnest` gives a clean many-to-one `job_categories` table that joins naturally.

## 1.6 — NumPy
**Where:** percentile computations in EDA and `app.py` (Wage Benchmarks)
**Why:** EP qualifying salary is literally a percentile policy ("top 1/3 of PMET").
`numpy.percentile` computes p33/p65/p90 for any category in one line.

## 1.7 — Pandas
**Where:** `01_clean_data.py` — vectorised `.str.strip`, `pd.to_datetime`, `.apply(parse_categories)`
**Why:** Each of the 16 rules is one or two vectorised ops — fast and auditable.

## 1.8 — EDA basic
**Where:** `03_eda_report.py`
**Why:** You cannot design a chart without first seeing shape, nulls, and describe().
It caught the $1 placeholders and the 999-vacancy cap.

## 1.9 — EDA advanced
**Where:** derived `open_days`, `apps_per_vacancy`, `is_part_time`, `is_pmet`
**Why:** The business question ("which roles are hard to fill?") is not a raw column —
it is a *derived* metric. EDA advanced is about building the metric, then checking it.

## 1.10 — Visualisation
**Where:** notebooks = Matplotlib/Seaborn, dashboard = Plotly
**Why:** Choose the chart to match the *decision*:
- **Ranked bar** = "which category is biggest?" (metric 1)
- **Scatter** = "are big-vacancy categories also high-paying?" (metric 2)
- **Horizontal bar with threshold line** = "how many are below the bar?" (mismatch)
- **Percentile line + annotated hlines** = "where is the market relative to policy?" (metric 6)
Colour-blind-safe palette + one-line "So what" captions serve non-technical stakeholders.