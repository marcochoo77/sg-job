"""
Streamlit dashboard for MOM Policy Officers — Work Pass analytics.

Design (why):
- st.metric: headline KPIs non-technical users read instantly.
- st.tabs: splits the 7 dashboard metrics into Overview / Hiring Health /
  Wage Benchmarks / Drill-down.
- st.sidebar.multiselect: filters a policy officer naturally asks for.
- Plotly: interactive tooltips + colour-blind-safe palette.
- st.cache_data: keeps the app fast on the full ~1M-row dataset.
- "Insight:" caption under every chart frames the finding as a decision,
  not just a visual (matches the brief's "Insight & story" criterion).

Run:  streamlit run app.py
"""
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "sg_jobs.duckdb"

BLUE, RED, GREEN, GREY = "#1F3864", "#C00000", "#548235", "#7F7F7F"
PALETTE = [BLUE, "#2E75B6", "#9DC3E6", GREEN, "#A9D18E", "#C55A11",
           "#F4B183", RED, "#FF7C80", GREY, "#BFBFBF", "#404040"]

st.set_page_config(page_title="SG Jobs Analytics — MOM", layout="wide",
                   page_icon="🇸🇬")


@st.cache_data(show_spinner="Loading jobs…")
def load():
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute("""
        SELECT c.*, jc.category_name
        FROM clean_jobs c
        LEFT JOIN job_categories jc ON c.metadata_jobPostId = jc.job_post_id
    """).df()
    con.close()
    for c in ("metadata_originalPostingDate", "metadata_expiryDate",
              "metadata_newPostingDate"):
        if c in df:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def insight(text: str):
    """One-line plain-English takeaway under each chart."""
    st.caption(f"**Insight:** {text}")


df = load()

# ---------------- Sidebar ----------------
st.sidebar.header("Filters")
cats = sorted(df["category_name"].dropna().unique())
f_cat = st.sidebar.multiselect("Job category", cats, default=[])
f_pmet = st.sidebar.multiselect("PMET", ["PMET", "Non-PMET", "Unknown"],
                                default=["PMET", "Non-PMET"])
sal_lo, sal_hi = st.sidebar.slider(
    "Monthly salary (S$)",
    int(np.nanmin(df["average_salary"])), int(np.nanmax(df["average_salary"])),
    (1800, 20000))

mask = df["is_pmet"].isin(f_pmet) & df["average_salary"].between(sal_lo, sal_hi)
if f_cat:
    mask &= df["category_name"].isin(f_cat)
view = df[mask]

# ---------------- Header + KPIs ----------------
st.title("🇸🇬 Singapore Jobs Analytics — Work-Pass Policy Dashboard")
st.caption("Persona: MOM Data Analyst · Audience: MOM Policy Officers "
           "(Work Permit · S Pass · EP)")
st.caption(f"Rows in view: **{len(view):,}** · Part-time/flexi flagged: "
           f"**{int(view['is_part_time'].sum()):,}**")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total vacancies", f"{int(view['numberOfVacancies'].sum()):,}")
k2.metric("Total applications",
          f"{int(view['metadata_totalNumberJobApplication'].sum()):,}")
k3.metric("Median monthly salary", f"S${view['average_salary'].median():,.0f}")
k4.metric("Avg open days", f"{view['open_days'].mean():.1f}")

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview", "🏥 Hiring Health", "💰 Wage Benchmarks", "🔎 Drill-down"])

# =====================================================================
# TAB 1 — Overview (metrics 1 & 2)
# =====================================================================
with tab1:
    # (2) Ranked bar — applications by category
    c1, c2 = st.columns(2)
    with c1:
        m1 = (view.groupby("category_name")["metadata_totalNumberJobApplication"]
                   .sum().sort_values(ascending=False).head(12).reset_index())
        fig = px.bar(m1, x="metadata_totalNumberJobApplication", y="category_name",
                     orientation="h", color_discrete_sequence=[BLUE],
                     labels={"metadata_totalNumberJobApplication": "Applications",
                             "category_name": ""},
                     title="Top categories by total applications")
        fig.update_layout(yaxis=dict(autorange="reversed"), height=440)
        st.plotly_chart(fig, use_container_width=True)
        insight("These categories draw the most applicant interest — "
                "the market's demand signal.")

    # (3) Scatter — vacancies vs mean salary
    with c2:
        m2 = (view.groupby("category_name")
                   .agg(vacancies=("numberOfVacancies", "sum"),
                        salary=("average_salary", "mean"))
                   .sort_values("vacancies", ascending=False).head(12).reset_index())
        fig = px.scatter(m2, x="vacancies", y="salary", text="category_name",
                         color="salary", color_continuous_scale="Blues",
                         labels={"vacancies": "Total vacancies",
                                 "salary": "Mean monthly salary (S$)"},
                         title="Vacancy count vs mean salary by category")
        fig.update_traces(textposition="top center")
        fig.update_layout(height=440, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        insight("Right-side categories need more headcount; high-y categories "
                "command higher wages.")

    # (4) Treemap — application share
    c3, c4 = st.columns(2)
    with c3:
        tm = (view.groupby("category_name")["metadata_totalNumberJobApplication"]
                   .sum().sort_values(ascending=False).head(15).reset_index())
        fig = px.treemap(tm, path=["category_name"],
                         values="metadata_totalNumberJobApplication",
                         color="metadata_totalNumberJobApplication",
                         color_continuous_scale="Blues",
                         title="Share of applications by category")
        fig.update_layout(height=440, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        insight("A few categories dominate total demand — quota planning "
                "should weight them most.")

    # (5) Stacked bar — PMET vs Non-PMET application share
    with c4:
        pm = (view.dropna(subset=["category_name"])
                   .groupby(["category_name", "is_pmet"])
                   ["metadata_totalNumberJobApplication"].sum().reset_index())
        tops = (pm.groupby("category_name")["metadata_totalNumberJobApplication"]
                  .sum().nlargest(10).index)
        pm = pm[pm["category_name"].isin(tops)]
        fig = px.bar(pm, x="metadata_totalNumberJobApplication", y="category_name",
                     color="is_pmet", orientation="h", barmode="stack",
                     color_discrete_map={"PMET": BLUE, "Non-PMET": GREEN,
                                         "Unknown": GREY},
                     labels={"metadata_totalNumberJobApplication": "Applications",
                             "category_name": "", "is_pmet": ""},
                     title="PMET vs Non-PMET application share")
        fig.update_layout(yaxis=dict(autorange="reversed"), height=440)
        st.plotly_chart(fig, use_container_width=True)
        insight("Categories dominated by PMET applications are the ones EP "
                "policy most directly affects.")

# =====================================================================
# TAB 2 — Hiring Health (metrics 3, 4, 5, 7)
# =====================================================================
with tab2:
    g = (view[~view["is_part_time"]]
         .groupby("category_name")
         .agg(vacancies=("numberOfVacancies", "sum"),
              apps=("metadata_totalNumberJobApplication", "sum"),
              open_days=("open_days", "mean"),
              reposts=("metadata_repostCount", "mean")).reset_index())
    g["mismatch"] = g["apps"] / g["vacancies"].replace(0, np.nan)

    # (6) Open days
    c1, c2 = st.columns(2)
    with c1:
        top = g.sort_values("open_days", ascending=False).head(12)
        fig = px.bar(top, x="open_days", y="category_name", orientation="h",
                     color="open_days", color_continuous_scale="Reds",
                     labels={"open_days": "Avg open days", "category_name": ""},
                     title="Hardest-to-fill categories (longest open days)")
        fig.update_layout(yaxis=dict(autorange="reversed"), height=440,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        insight("Longer bars = roles that stay unfilled — review quota or "
                "SOL eligibility.")

    # (7) Reposts
    with c2:
        top = g.sort_values("reposts", ascending=False).head(12)
        fig = px.bar(top, x="reposts", y="category_name", orientation="h",
                     color="reposts", color_continuous_scale="Oranges",
                     labels={"reposts": "Avg reposts", "category_name": ""},
                     title="Most re-posted categories (chronic bottlenecks)")
        fig.update_layout(yaxis=dict(autorange="reversed"), height=440,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        insight("Frequent re-posting means employers cannot fill these in "
                "one cycle — a persistent shortage.")

    # (8) Mismatch diverging bar
    st.subheader("Talent Scarcity & Mismatch Index  (applications ÷ vacancies)")
    gm = g.dropna(subset=["mismatch"]).sort_values("mismatch")
    gm["band"] = np.where(gm["mismatch"] < 1, "Shortage (<1.0)", "Healthy (≥1.0)")
    fig = px.bar(gm, x="mismatch", y="category_name", orientation="h",
                 color="band",
                 color_discrete_map={"Shortage (<1.0)": RED,
                                     "Healthy (≥1.0)": GREEN},
                 labels={"mismatch": "apps / vacancies", "category_name": "",
                         "band": ""},
                 title="Ratios below 1.0 signal acute local shortage")
    fig.add_vline(x=1.0, line_dash="dash", line_color=GREY)
    fig.update_layout(yaxis=dict(autorange="reversed"), height=520)
    st.plotly_chart(fig, use_container_width=True)
    insight("Red-side categories have more vacancies than applicants — "
            "prime candidates for SOL listing or quota relief.")

    # (9) Boxplot — open-days distribution
    # (10) Scatter — shortage quadrant
    c3, c4 = st.columns(2)
    with c3:
        tops = (view.groupby("category_name")["open_days"].mean()
                    .nlargest(8).index)
        b = view[view["category_name"].isin(tops)][["category_name", "open_days"]].dropna()
        fig = px.box(b, x="open_days", y="category_name", color="category_name",
                     color_discrete_sequence=PALETTE,
                     labels={"open_days": "Open days", "category_name": ""},
                     title="Open-days spread for slowest-filling categories")
        fig.update_layout(height=440, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        insight("Wide boxes mean the delay hits every posting; narrow boxes "
                "mean a few outliers pull the average up.")

    with c4:
        g2 = g.copy()
        g2["mean_salary"] = (view.groupby("category_name")["average_salary"]
                                 .mean().reindex(g2["category_name"]).values)
        fig = px.scatter(g2, x="vacancies", y="apps", text="category_name",
                         size="mean_salary", size_max=45,
                         color="mismatch", color_continuous_scale="RdYlGn_r",
                         labels={"vacancies": "Total vacancies",
                                 "apps": "Total applications",
                                 "mismatch": "apps/vacancies"},
                         title="Shortage quadrant: high vacancies, low applications")
        fig.add_shape(type="line", x0=g2["vacancies"].median(), x1=g2["vacancies"].median(),
                      y0=0, y1=g2["apps"].max(), line=dict(dash="dash", color=GREY))
        fig.update_traces(textposition="top center")
        fig.update_layout(height=440)
        st.plotly_chart(fig, use_container_width=True)
        insight("Bubble size = mean salary. The lower-right quadrant is where "
                "quota pressure will bite hardest.")

# =====================================================================
# TAB 3 — Wage Benchmarks (metric 6)
# =====================================================================
with tab3:
    st.markdown("### PMET wage benchmarks vs S Pass / EP qualifying salaries")
    st.caption("Part-time roles are assessed **hourly** under LQS and are "
               "excluded from this monthly view.")
    pmet = view[(view["is_pmet"] == "PMET") & (~view["is_part_time"])]
    pmet = pmet.dropna(subset=["average_salary"])

    # (11) Percentile line
    pct = (pmet.groupby("category_name")["average_salary"]
           .agg(p33=lambda s: np.percentile(s, 33), p50="median",
                p65=lambda s: np.percentile(s, 65),
                p90=lambda s: np.percentile(s, 90))
           .reset_index().sort_values("p50", ascending=False))
    fig = px.line(pct.melt(id_vars="category_name"), x="variable", y="value",
                  color="category_name", markers=True, color_discrete_sequence=PALETTE,
                  labels={"variable": "Percentile", "value": "Monthly salary (S$)",
                          "category_name": "Category"},
                  title="PMET wage percentiles by category")
    fig.add_hline(y=3300, line_dash="dot", line_color=GREEN,
                  annotation_text="S Pass $3,300", annotation_position="top left")
    fig.add_hline(y=5600, line_dash="dot", line_color=RED,
                  annotation_text="EP $5,600", annotation_position="top left")
    fig.update_layout(height=560, legend_title="")
    st.plotly_chart(fig, use_container_width=True)
    insight("Where the p33–p65 range sits well above the EP bar, policy is "
            "aligned; where it sits below, the category may warrant a "
            "sector-specific review.")

    # (12) Grouped bar — p50 by category, PMET vs Non-PMET
    # (13) Histogram — PMET salary distribution with thresholds
    c1, c2 = st.columns(2)
    with c1:
        grp = (view.dropna(subset=["average_salary", "category_name"])
                   .groupby(["category_name", "is_pmet"])["average_salary"]
                   .median().reset_index())
        tops = (grp.groupby("category_name")["average_salary"]
                   .max().nlargest(10).index)
        grp = grp[grp["category_name"].isin(tops)]
        fig = px.bar(grp, x="average_salary", y="category_name",
                     color="is_pmet", barmode="group", orientation="h",
                     color_discrete_map={"PMET": BLUE, "Non-PMET": GREEN,
                                         "Unknown": GREY},
                     labels={"average_salary": "Median monthly salary (S$)",
                             "category_name": "", "is_pmet": ""},
                     title="PMET premium: median salary by category")
        fig.update_layout(yaxis=dict(autorange="reversed"), height=480)
        st.plotly_chart(fig, use_container_width=True)
        insight("The gap between blue and green is the PMET premium — the "
                "policy lever EP thresholds act on.")

    with c2:
        fig = px.histogram(pmet, x="average_salary", nbins=60,
                           color_discrete_sequence=[BLUE],
                           labels={"average_salary": "Monthly salary (S$)"},
                           title="PMET salary distribution vs thresholds")
        fig.add_vline(x=3300, line_dash="dot", line_color=GREEN,
                      annotation_text="S Pass $3,300")
        fig.add_vline(x=5600, line_dash="dot", line_color=RED,
                      annotation_text="EP $5,600")
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)
        insight("Share of PMET jobs to the right of each line = share "
                "clearing that pass bar.")

    # (14) Heatmap — category × percentile
    st.subheader("Percentile heatmap — compare all categories at a glance")
    heat = pct.set_index("category_name")[["p33", "p50", "p65", "p90"]]
    fig = px.imshow(heat, text_auto=".0f", aspect="auto",
                    color_continuous_scale="Blues",
                    labels=dict(x="Percentile", y="Category", color="S$"),
                    title="Monthly salary percentiles (S$) by category")
    fig.update_layout(height=520)
    st.plotly_chart(fig, use_container_width=True)
    insight("One glance shows which categories have both high medians and "
            "wide p90 gaps — the two features EP policy cares about.")

# =====================================================================
# TAB 4 — Drill-down
# =====================================================================
with tab4:
    # (15) Salary distribution for the current filter
    # (16) Postings over time (first posted vs reposted)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(view.dropna(subset=["average_salary"]),
                           x="average_salary", nbins=60, color="is_pmet",
                           color_discrete_map={"PMET": BLUE, "Non-PMET": GREEN,
                                               "Unknown": GREY},
                           labels={"average_salary": "Monthly salary (S$)",
                                   "is_pmet": ""},
                           title="Salary distribution (current filters)")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)
        insight("Check the shape of your filtered slice — median alone can "
                "hide a bimodal market.")

    with c2:
        tt = view.dropna(subset=["metadata_originalPostingDate"]).copy()
        if tt.empty:
            st.info("No dated postings in the current filter.")
        else:
            tt["month_orig"] = (tt["metadata_originalPostingDate"]
                                .dt.to_period("M").dt.to_timestamp())
            tt["month_new"] = (tt["metadata_newPostingDate"]
                               .dt.to_period("M").dt.to_timestamp())

            # Build each series as its own 3-column frame
            orig = (tt.groupby("month_orig").size()
                      .reset_index(name="count"))
            orig["series"] = "first posted"
            orig = orig.rename(columns={"month_orig": "month"})

            new = (tt.groupby("month_new").size()
                     .reset_index(name="count"))
            new["series"] = "reposted"
            new = new.rename(columns={"month_new": "month"})

            ts = (pd.concat([orig, new], ignore_index=True)
                    .dropna(subset=["month"]))

            if ts.empty:
                st.info("No dated postings in the current filter.")
            else:
                fig = px.line(ts, x="month", y="count", color="series",
                              markers=True,
                              color_discrete_map={"first posted": BLUE,
                                                  "reposted": RED},
                              labels={"month": "", "count": "Postings",
                                      "series": ""},
                              title="Postings over time — first posted vs reposted")
                fig.update_layout(height=420)
                st.plotly_chart(fig, use_container_width=True)
                insight("A rising red line against a flat blue line means the "
                        "market is re-posting more than creating new roles.")

    st.markdown("### Filtered job postings")
    cols = [c for c in ["title", "postedCompany_name", "category_name", "is_pmet",
                        "average_salary", "numberOfVacancies", "open_days",
                        "metadata_repostCount", "employmentTypes"]
            if c in view.columns]
    st.dataframe(view[cols].sort_values("average_salary", ascending=False).head(2000),
                 use_container_width=True, height=500)
    insight("Use this table to inspect the individual postings behind any "
            "chart above.")

st.divider()