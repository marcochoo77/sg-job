"""
Batch 1 — Extract & normalise.

What it does
------------
1. Auto-unzips SGJobData.csv.zip if present.
2. Loads a 50k sample (default) or the full ~1M rows (--full) into DuckDB.
3. Rebuilds the `job_categories` table from the raw JSON `categories`
   column using your group's exact unnest + json_extract SQL.
4. Exports:
   - data/raw_jobs_sample.csv
   - data/raw_jobs_full.csv        (only with --full)
   - data/job_categories.csv
   - data/sg_jobs.duckdb           (tables: raw_jobs, job_categories)

Why (lessons 1.1–1.5)
---------------------
- 1.1 Intro: sample-first ("taste a spoonful before cooking the whole pot").
- 1.2 Intro DB: DuckDB as a file-based analytical DB.
- 1.3 DDL: CREATE TABLE for raw_jobs, job_categories.
- 1.4 DML: INSERT / SELECT / COPY.
- 1.5 Advanced SQL: unnest + json_extract_string to normalise a JSON array.

Run
---
    python scripts/00_extract_data.py                 # 50k sample
    python scripts/00_extract_data.py --full          # full ~1M rows
    python scripts/00_extract_data.py --input data/SGJobData.csv.zip
"""
from __future__ import annotations
import argparse, zipfile, sys
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "sg_jobs.duckdb"


def resolve_input(user_path: str | None) -> Path:
    if user_path:
        p = Path(user_path)
        if not p.exists():
            sys.exit(f"[ERR] Input not found: {p}")
        return p
    for name in ("SGJobData.csv", "SGJobData.csv.zip", "sg_jobs.csv"):
        p = DATA / name
        if p.exists():
            return p
    sys.exit("[ERR] Put SGJobData.csv (or .zip) into data/ or pass --input")


def unzip_if_needed(path: Path) -> Path:
    if path.suffix.lower() != ".zip":
        return path
    out = path.with_suffix("")  # strip .zip
    if not out.exists():
        print(f"[info] Unzipping {path.name} -> {out.name}")
        with zipfile.ZipFile(path) as z:
            z.extractall(DATA)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=None, help="path to SGJobData.csv or .zip")
    ap.add_argument("--full", action="store_true", help="load all rows (~1M)")
    ap.add_argument("--sample", type=int, default=50_000)
    args = ap.parse_args()

    csv_path = unzip_if_needed(resolve_input(args.input))
    print(f"[1/4] Reading CSV: {csv_path}")

    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS raw_jobs")
    con.execute("DROP TABLE IF EXISTS job_categories")

    n = "" if args.full else f" LIMIT {args.sample}"
    con.execute(f"""
        CREATE TABLE raw_jobs AS
        SELECT * FROM read_csv_auto('{csv_path.as_posix()}')
        {n};
    """)
    total = con.execute("SELECT COUNT(*) FROM raw_jobs").fetchone()[0]
    print(f"      raw_jobs rows: {total:,}  cols: {len(con.execute('DESCRIBE raw_jobs').fetchall())}")

    print("[2/4] Exporting raw_jobs_sample.csv (or full)...")
    out_name = "raw_jobs_full.csv" if args.full else "raw_jobs_sample.csv"
    con.execute(f"COPY raw_jobs TO '{(DATA/out_name).as_posix()}' (HEADER, DELIMITER ',');")

    print("[3/4] Building job_categories (unnest JSON)...")
    con.execute("""
        CREATE TABLE job_categories AS
        SELECT
            metadata_jobPostId                                   AS job_post_id,
            CAST(json_extract_string(unnested, '$.id') AS INTEGER) AS category_id,
            json_extract_string(unnested, '$.category')          AS category_name
        FROM (
            SELECT
                metadata_jobPostId,
                unnest(CAST(json_extract(categories, '$[*]') AS JSON[])) AS unnested
            FROM raw_jobs
            WHERE categories IS NOT NULL
              AND json_valid(categories)
        );
    """)
    ncat = con.execute("SELECT COUNT(*) FROM job_categories").fetchone()[0]
    nuniq = con.execute("SELECT COUNT(DISTINCT category_name) FROM job_categories").fetchone()[0]
    print(f"      job_categories rows: {ncat:,}  distinct categories: {nuniq}")

    print("[4/4] Exporting job_categories.csv...")
    con.execute(f"COPY job_categories TO '{(DATA/'job_categories.csv').as_posix()}' (HEADER, DELIMITER ',');")
    con.close()
    print(f"[done] DB at {DB_PATH}")


if __name__ == "__main__":
    main()