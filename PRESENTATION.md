# 10-minute presentation — speaker notes

## Slide 1 — Business case (2 min)
- **Persona:** MOM Data Analyst.
- **Audience:** MOM Policy Officers (Work Permit / S Pass / EP).
- **Decision supported:** how many passes, at what salary bands, for which categories.
- **Success:** a policy officer can answer "Is category X hot, under-filled, or over-supplied?"
  in <30 seconds on one screen.

## Slide 2 — Data & process (3 min)
- ~1M-row CSV → **sample first (50k)** → **DuckDB** (file DB).
- Rebuild `job_categories` with `unnest`+`json_extract` (lesson 1.5).
- Apply 16 cleaning rules **with row-drop logging** (rule 15 = LQS $1,800).
- Engineer `open_days`, `apps_per_vacancy`, `is_pmet`, `is_part_time`.
- Explain *why*: each metric must be a decision, not a chart.

## Slide 3 — Dashboard walkthrough (3 min)
1. Overview — applications & vacancies/salary scatter.
2. Hiring Health — open-days, reposts, **mismatch index vs 1.0 line**.
3. Wage Benchmarks — PMET percentiles vs **S Pass $3,300 / EP $5,600** lines.
4. Drill-down — filter and inspect postings.
- Show the sidebar filters (category, PMET, salary).

## Slide 4 — Challenges & learnings (2 min)
- Cleaning `$1` placeholders and yearly/monthly salary mixing.
- LQS judges part-timers hourly, so we exclude them only from the monthly-band chart.
- Lesson: **visualisation is a policy argument** — the threshold lines do the talking.
- Next steps: sector split (Financial Services vs others), time-trend tab, SOL tagging.