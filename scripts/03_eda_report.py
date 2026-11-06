"""
Batch 1 — First-look EDA printed to console (learning output).

Covers lesson 1.6 (NumPy stats), 1.7 (Pandas), 1.8 (basic EDA).
Run AFTER 00_extract_data.py.
"""
from __future__ import annotations
from pathlib import Path
import duckdb, numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "sg_jobs.duckdb"

def hr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)

def main():
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute("SELECT * FROM raw_jobs").df()
    cats = con.execute("SELECT * FROM job_categories").df()
    con.close()

    hr("1) Shape & dtypes")
    print(df.shape); print(df.dtypes)

    hr("2) Null counts (top 15)")
    print(df.isna().sum().sort_values(ascending=False).head(15))

    hr("3) Salary stats (NumPy) — why: 1.6 shows raw distribution before cleaning")
    for c in ("average_salary", "salary_minimum", "salary_maximum"):
        if c in df:
            s = pd.to_numeric(df[c], errors="coerce").dropna().to_numpy()
            print(f"{c:18s} n={len(s):>7,}  min={s.min():>10,.0f}  "
                  f"p33={np.percentile(s,33):>9,.0f}  p50={np.percentile(s,50):>9,.0f}  "
                  f"p90={np.percentile(s,90):>9,.0f}  max={s.max():>10,.0f}")

    hr("4) Top 15 categories (Pandas groupby) — why: demand map")
    print(cats["category_name"].value_counts().head(15))

    hr("5) positionLevels distribution — why: PMET mapping (rule 11)")
    if "positionLevels" in df:
        print(df["positionLevels"].value_counts(dropna=False))

    hr("6) Repost / vacancies / applications summary — why: hiring-health metrics")
    for c in ("metadata_repostCount", "numberOfVacancies",
              "metadata_totalNumberJobApplication", "minimumYearsExperience"):
        if c in df:
            s = pd.to_numeric(df[c], errors="coerce")
            print(f"{c:38s} mean={s.mean():>8.2f}  p50={s.median():>8.1f}  max={s.max():>8.0f}")

if __name__ == "__main__":
    main()