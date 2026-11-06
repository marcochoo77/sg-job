"""
Batch 2 — Verify DB contents and print schema (quick sanity check).

Why (1.3 DDL / 1.4 DML): confirms tables, row counts and column types.
"""
from pathlib import Path
import duckdb
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "sg_jobs.duckdb"

def main():
    con = duckdb.connect(str(DB), read_only=True)
    for t in ("raw_jobs", "job_categories", "clean_jobs"):
        try:
            n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"{t:16s} rows={n:,}")
        except Exception as e:
            print(f"{t:16s} MISSING ({e})")
    print("\nclean_jobs schema:")
    print(con.execute("DESCRIBE clean_jobs").df().to_string(index=False))
    con.close()

if __name__ == "__main__":
    main()