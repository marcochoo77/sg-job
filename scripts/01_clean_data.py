"""
Batch 2 — Apply ALL 16 group cleaning rules + feature engineering.

Every rule prints how many rows it drops/flags — this is the "explain your
cleaning" requirement from the brief.

Outputs
-------
data/sg_jobs_clean.csv   (cleaned + engineered)
data/clean_jobs          (DuckDB table)

Why (lessons 1.7–1.9)
---------------------
- 1.7 Pandas: vectorised cleaning, .str.strip, pd.to_datetime, .apply(parse_json_list).
- 1.8 EDA basic: recompute describe() after each rule to verify.
- 1.9 EDA advanced: derive mismatch index, open days, PMET flag.
"""
from __future__ import annotations
import json, re
from pathlib import Path
import duckdb, numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "sg_jobs.duckdb"
OUT = ROOT / "data" / "sg_jobs_clean.csv"

PMET_LEVELS = {"Professional", "Manager", "Middle Management",
               "Senior Management", "Executive", "Senior Executive"}
NONPMET_LEVELS = {"Non-executive", "Fresh/entry", "Junior Executive"}

def log(step, msg): print(f"[{step:>2}] {msg}")

def parse_categories(s):
    """JSON array of dicts -> list of (id, name). Robust to junk."""
    if not isinstance(s, str) or not s.strip():
        return []
    try:
        arr = json.loads(s)
        return [(int(d.get("id")), str(d.get("category")).strip())
                for d in arr if isinstance(d, dict)]
    except Exception:
        return []

def main():
    con = duckdb.connect(str(DB))
    df = con.execute("SELECT * FROM raw_jobs").df()
    n0 = len(df); log(0, f"loaded raw_jobs rows={n0:,}")

    # Rule 13: drop fully-null rows
    before = len(df); df = df.dropna(how="all"); log(13, f"drop all-null rows: -{before-len(df)}")

    # Rule 16: strip whitespace on text fields
    for c in ("title", "postedCompany_name"):
        if c in df: df[c] = df[c].astype("string").str.strip()

    # Rules 1–4: $1 placeholders -> NaN in salary fields
    for c in ("average_salary", "salary_minimum", "salary_maximum"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            n1 = (df[c] == 1).sum()
            df.loc[df[c] == 1, c] = np.nan
            log(f"1-4", f"{c}: $1 -> null  (n={n1})")

    # Rules 7–9: yearly/monthly mix — drop (group decision)
    if {"salary_minimum", "salary_maximum"}.issubset(df.columns):
        yearly_like = (df["salary_maximum"] > 30000) | (df["salary_minimum"] > 30000)
        before = len(df); df = df[~yearly_like]
        log("7-9", f"drop yearly-vs-monthly ambiguous rows: -{before-len(df)}")

    # Rule 2: average_salary > 205000 -> drop
    before = len(df); df = df[df["average_salary"].isna() | (df["average_salary"] <= 205000)]
    log(2, f"drop avg_salary>205000: -{before-len(df)}")

    # Rule 5: numberOfVacancies == 999 -> drop
    if "numberOfVacancies" in df:
        before = len(df); df = df[df["numberOfVacancies"] != 999]
        log(5, f"drop vacancies==999: -{before-len(df)}")

    # Rule 6: minimumYearsExperience > 20 -> drop
    if "minimumYearsExperience" in df:
        before = len(df); df = df[df["minimumYearsExperience"].fillna(0) <= 20]
        log(6, f"drop experience>20y: -{before-len(df)}")

    # Rule 14: drop occupationID & status_id (constant/missing)
    for c in ("occupationID", "status_id"):
        if c in df.columns: df = df.drop(columns=[c]); log(14, f"dropped column {c}")

    # Rule 15: LQS — drop avg_salary < 1800 (group decision, literal)
    before = len(df); df = df[df["average_salary"].isna() | (df["average_salary"] >= 1800)]
    log(15, f"drop avg_salary<1800 (LQS): -{before-len(df)}")

    # Rule 10: parse dates
    date_cols = [c for c in ("metadata_newPostingDate", "metadata_originalPostingDate",
                             "metadata_expiryDate") if c in df.columns]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce", utc=True).dt.tz_localize(None)
    log(10, f"parsed dates: {date_cols}")

    # Rule 11: PMET mapping
    def pmet(p):
        if p in PMET_LEVELS: return "PMET"
        if p in NONPMET_LEVELS: return "Non-PMET"
        return "Unknown"
    df["is_pmet"] = df.get("positionLevels", pd.Series(dtype="object")).map(pmet)
    log(11, "is_pmet: " + str(df["is_pmet"].value_counts().to_dict()))

    # Rule 12: rebuild categories per row (also in job_categories table)
    cats_per_row = df.get("categories", pd.Series(dtype="object")).map(parse_categories)
    df["n_categories"] = cats_per_row.map(len)
    df["primary_category"] = cats_per_row.map(lambda L: L[0][1] if L else None)
    if "categories" in df.columns:
        df = df.drop(columns=["categories"]); log(12, "dropped raw categories column (normalised separately)")

    # Feature engineering (1.9 EDA advanced)
    df["open_days"] = (df["metadata_expiryDate"] - df["metadata_originalPostingDate"]).dt.days
    df["apps_per_vacancy"] = (df["metadata_totalNumberJobApplication"]
                              / df["numberOfVacancies"].replace(0, np.nan))
    df["is_part_time"] = (df.get("employmentTypes", pd.Series(dtype="object"))
                          .astype("string").str.contains("part time|flexi", case=False, na=False))

    # Rewrite into DuckDB
    con.execute("DROP TABLE IF EXISTS clean_jobs")
    con.execute("CREATE TABLE clean_jobs AS SELECT * FROM df")
    df.to_csv(OUT, index=False)
    log("done", f"clean rows={len(df):,}  saved -> {OUT}")
    con.close()

if __name__ == "__main__":
    main()