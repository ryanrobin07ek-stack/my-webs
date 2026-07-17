import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Job Skills Analytics", page_icon="📊", layout="wide")

PALETTE = ["#8B5CF6", "#22D3EE", "#EC4899", "#D946EF", "#38BDF8"]


@st.cache_data
def load_skills():
    return pd.read_csv("cleaned_skills_count.csv")


@st.cache_data
def load_posts():
    df = pd.read_csv("all_job_post.csv", usecols=["job_id", "category", "job_title", "job_skill_set"])
    df["skill_count"] = df["job_skill_set"].str.count(",") + 1
    return df.drop(columns=["job_skill_set"])


skills_df = load_skills()
posts_df = load_posts()
CATEGORIES = sorted(skills_df["category"].unique())

if "page" not in st.session_state:
    st.session_state.page = "Overview"
if "cat_filter" not in st.session_state:
    st.session_state.cat_filter = CATEGORIES.copy()


def go_to(page_name):
    st.session_state.page = page_name


# ---------- one big CSS block, this is what makes it look like a real product ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* dark canvas behind everything so the dashboard reads as a floating card */
    .stApp { background-color: #05070d; }

    section.main > div.block-container {
        background: linear-gradient(180deg, #0d1224 0%, #0b0f1f 100%);
        border: 1px solid #1e2540;
        border-radius: 22px;
        padding: 28px 32px 40px 32px;
        margin-top: 18px;
        box-shadow: 0 25px 60px rgba(0,0,0,.55);
        max-width: 1400px;
    }

    section[data-testid="stSidebar"] {
        background-color: #0d1224 !important;
        border-right: 1px solid #1e2540;
    }
    section[data-testid="stSidebar"] > div { padding-top: 10px; }

    h1, h2, h3 { color: #fff; }
    .stCaption, p { color: #94A3B8; }

    /* top header bar */
    .dash-header {
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 22px; padding-bottom: 18px; border-bottom: 1px solid #1e2540;
    }
    .dash-title { font-size: 24px; font-weight: 800; color: #fff; margin: 0; }
    .dash-sub { font-size: 13px; color: #6b7690; margin-top: 2px; }
    .pill-badge {
        background: rgba(139,92,246,.15); color: #c4b5fd; border: 1px solid rgba(139,92,246,.35);
        border-radius: 20px; padding: 5px 14px; font-size: 12px; font-weight: 600;
    }

    /* kpi cards */
    .kpi-card {
        background: #141a2e; border: 1px solid #1e2540; border-radius: 16px;
        padding: 16px 18px; height: 118px; position: relative; overflow: hidden;
    }
    .kpi-card::after {
        content: ""; position: absolute; top: -30px; right: -30px; width: 90px; height: 90px;
        border-radius: 50%; background: var(--glow, #8B5CF6); opacity: .12;
    }
    .kpi-icon {
        width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center;
        justify-content: center; font-size: 16px; background: var(--glow, #8B5CF6); margin-bottom: 10px;
    }
    .kpi-num { font-size: 24px; font-weight: 800; color: #fff; line-height: 1; }
    .kpi-label { font-size: 11px; color: #8891a8; text-transform: uppercase; letter-spacing: .06em; margin-top: 4px; }
    .kpi-sub { font-size: 11px; color: #5ee6c4; margin-top: 6px; font-weight: 600; }

    /* generic content card */
    div.glass-card {
        background-color: #141a2e; border: 1px solid #1e2540; border-radius: 16px;
        padding: 20px; margin-bottom: 18px;
    }
    .card-title { color: #fff; font-size: 14px; font-weight: 700; margin-bottom: 2px; }
    .card-title-sub { color: #6b7690; font-size: 11px; margin-bottom: 14px; }

    /* executive summary list */
    .exec-item {
        display: flex; align-items: flex-start; gap: 10px; padding: 10px 0;
        border-bottom: 1px dashed #1e2540; font-size: 13px; color: #cbd5e1;
    }
    .exec-item:last-child { border-bottom: none; }
    .exec-dot {
        width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; flex-shrink: 0;
    }

    /* sidebar nav as filled pills */
    .stButton > button {
        width: 100%; text-align: left; background: transparent; color: #94A3B8;
        border: 1px solid transparent; padding: 10px 14px; border-radius: 10px;
        font-size: 14px; font-weight: 600; margin-bottom: 4px;
    }
    .stButton > button:hover { background: rgba(139,92,246,.14); color: #fff; border-color: #2d2f5e; }

    div[data-testid="stMetric"] {
        background-color: #141a2e; border: 1px solid #1e2540; border-radius: 12px; padding: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def kpi(col, icon, label, num, sub, color):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card" style="--glow:{color}">
                <div class="kpi-icon" style="background:{color}22; color:{color}">{icon}</div>
                <div class="kpi-num">{num}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def card_open(title, sub=""):
    st.markdown(
        f"<div class='glass-card'><div class='card-title'>{title}</div>"
        + (f"<div class='card-title-sub'>{sub}</div>" if sub else ""),
        unsafe_allow_html=True,
    )


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)


# ---------- sidebar ----------
with st.sidebar:
    st.markdown("<h2 style='color:#fff;font-size:19px;font-weight:800;margin-bottom:0;'>📊 Job Skills</h2>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6b7690;font-size:12px;margin-bottom:18px;'>Live job market analytics</div>", unsafe_allow_html=True)

    for p, icon in [("Overview", "🏠"), ("Category Deep-Dive", "🔍"), ("Job Explorer", "🗂️"), ("About", "ℹ️")]:
        active = st.session_state.page == p
        label = f"{'🟣' if active else icon}  {p}"
        if st.button(label, key=f"nav_{p}"):
            go_to(p)
            st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#8B5CF6;font-size:11px;font-weight:700;letter-spacing:.1em;'>FILTER</div>", unsafe_allow_html=True)
    st.session_state.cat_filter = st.multiselect("Category", CATEGORIES, default=st.session_state.cat_filter, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    if c1.button("↺ Reset"):
        st.session_state.cat_filter = CATEGORIES.copy()
        st.rerun()
    if c2.button("✕ Clear"):
        st.session_state.cat_filter = []
        st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.download_button(
        "⬇ Export filtered CSV",
        data=skills_df[skills_df["category"].isin(st.session_state.cat_filter or CATEGORIES)].to_csv(index=False),
        file_name="filtered_skills.csv", mime="text/csv", use_container_width=True,
    )

active_cats = st.session_state.cat_filter or CATEGORIES
skills_view = skills_df[skills_df["category"].isin(active_cats)]
posts_view = posts_df[posts_df["category"].isin(active_cats)]

# =========================================================
# OVERVIEW
# =========================================================
if st.session_state.page == "Overview":
    st.markdown(
        f"""
        <div class="dash-header">
            <div>
                <p class="dash-title">Job Skills Overview</p>
                <p class="dash-sub">What employers are actually asking for, straight from the raw postings</p>
            </div>
            <div class="pill-badge">{len(active_cats)} of {len(CATEGORIES)} categories active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_posts = len(posts_view)
    unique_skills = skills_view["skills"].nunique()
    avg_skills = round(skills_view["job_count"].sum() / max(total_posts, 1), 1)

    by_cat_posts = posts_view["category"].value_counts()
    top_cat = by_cat_posts.idxmax() if total_posts else "-"
    top_cat_share = round(by_cat_posts.max() / total_posts * 100) if total_posts else 0

    by_skill = skills_view.groupby("skills")["job_count"].sum().sort_values(ascending=False)
    top_skill = by_skill.index[0] if len(by_skill) else "-"
    top_skill_share = round(by_skill.iloc[0] / total_posts * 100) if total_posts and len(by_skill) else 0

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi(k1, "💼", "Job Postings", f"{total_posts:,}", f"{len(active_cats)} categories", "#8B5CF6")
    kpi(k2, "🧠", "Unique Skills", f"{unique_skills:,}", "distinct mentions", "#22D3EE")
    kpi(k3, "📈", "Avg Skills / Post", avg_skills, "per listing", "#EC4899")
    kpi(k4, "🏆", "Top Skill", top_skill.title()[:14], f"in {top_skill_share}% of posts", "#D946EF")
    kpi(k5, "🏷️", "Top Category", top_cat.title()[:14], f"{top_cat_share}% of postings", "#38BDF8")
    kpi(k6, "📊", "Categories", len(active_cats), "in current view", "#22C55E")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    left, right = st.columns([2.2, 1])

    with left:
        card_open("Most requested skills", "Ranked by how many postings mention them")
        top_n = st.slider("Show top N", 5, 30, 15, label_visibility="collapsed")
        top_skills = by_skill.head(top_n).sort_values()
        fig = go.Figure(go.Bar(
            x=top_skills.values, y=top_skills.index, orientation="h",
            marker=dict(color=top_skills.values, colorscale=[[0, "#22D3EE"], [1, "#8B5CF6"]]),
            text=top_skills.values, textposition="outside",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8"), xaxis=dict(showgrid=True, gridcolor="#1e2540"),
            margin=dict(l=10, r=30, t=10, b=10), height=440,
        )
        st.plotly_chart(fig, use_container_width=True)
        card_close()

    with right:
        card_open("Executive summary")
        items = [
            ("#8B5CF6", f"<b>{top_skill.title()}</b> is the most in-demand skill — mentioned in {top_skill_share}% of live postings."),
            ("#22D3EE", f"<b>{top_cat.title()}</b> leads posting volume with {by_cat_posts.max()} listings ({top_cat_share}%)."),
            ("#EC4899", f"Postings mention <b>{avg_skills} skills</b> on average."),
            ("#D946EF", f"<b>{unique_skills:,}</b> distinct skill mentions tracked across the filtered set."),
            ("#38BDF8", f"Dataset covers <b>{total_posts:,}</b> postings across {len(active_cats)} categories."),
        ]
        for color, text in items:
            st.markdown(
                f"<div class='exec-item'><div class='exec-dot' style='background:{color}'></div><div>{text}</div></div>",
                unsafe_allow_html=True,
            )
        card_close()

    b1, b2, b3 = st.columns(3)

    with b1:
        card_open("Postings by category")
        fig2 = go.Figure(go.Pie(
            values=by_cat_posts.values, labels=[c.title() for c in by_cat_posts.index], hole=0.65,
            marker=dict(colors=PALETTE), textinfo="percent", textfont=dict(color="#fff", size=11),
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"),
            legend=dict(orientation="h", y=-0.15, font=dict(size=9)), margin=dict(l=10, r=10, t=10, b=10), height=300,
        )
        st.plotly_chart(fig2, use_container_width=True)
        card_close()

    with b2:
        card_open("Top 5 job titles")
        top_titles = posts_view["job_title"].value_counts().head(5).sort_values()
        fig3 = go.Figure(go.Bar(
            x=top_titles.values, y=top_titles.index, orientation="h",
            marker=dict(color="#8B5CF6"), text=top_titles.values, textposition="outside",
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8", size=10),
            xaxis=dict(showgrid=False), margin=dict(l=10, r=25, t=10, b=10), height=300,
        )
        st.plotly_chart(fig3, use_container_width=True)
        card_close()

    with b3:
        card_open("Avg skills / posting by category")
        avg_by_cat = (skills_view.groupby("category")["job_count"].sum() / posts_view["category"].value_counts()).round(1).sort_values()
        fig4 = go.Figure(go.Bar(
            x=avg_by_cat.values, y=[c.title() for c in avg_by_cat.index], orientation="h",
            marker=dict(color="#22D3EE"), text=avg_by_cat.values, textposition="outside",
        ))
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8", size=10),
            xaxis=dict(showgrid=False), margin=dict(l=10, r=25, t=10, b=10), height=300,
        )
        st.plotly_chart(fig4, use_container_width=True)
        card_close()

# =========================================================
# CATEGORY DEEP-DIVE
# =========================================================
elif st.session_state.page == "Category Deep-Dive":
    st.markdown(
        "<div class='dash-header'><div><p class='dash-title'>Category Deep-Dive</p>"
        "<p class='dash-sub'>Drill into one category at a time</p></div></div>",
        unsafe_allow_html=True,
    )
    cat = st.selectbox("Category", CATEGORIES)
    sub = skills_df[skills_df["category"] == cat]
    sub_posts = posts_df[posts_df["category"] == cat]

    m1, m2, m3 = st.columns(3)
    kpi(m1, "💼", "Postings", len(sub_posts), cat.title(), "#8B5CF6")
    kpi(m2, "🧠", "Unique Skills", sub["skills"].nunique(), "in this category", "#22D3EE")
    kpi(m3, "📈", "Avg Skills / Post", round(sub["job_count"].sum() / max(len(sub_posts), 1), 1), "per listing", "#EC4899")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        card_open(f"Top skills in {cat.title()}")
        top15 = sub.groupby("skills")["job_count"].sum().sort_values(ascending=False).head(15).sort_values()
        fig5 = go.Figure(go.Bar(x=top15.values, y=top15.index, orientation="h", marker=dict(color="#8B5CF6")))
        fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"), margin=dict(l=10, r=10, t=10, b=10), height=430)
        st.plotly_chart(fig5, use_container_width=True)
        card_close()

    with col_b:
        card_open("Most common job titles")
        top_titles = sub_posts["job_title"].value_counts().head(10)
        fig6 = go.Figure(go.Bar(x=top_titles.index, y=top_titles.values, marker=dict(color="#22D3EE")))
        fig6.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"), xaxis=dict(tickangle=-35), margin=dict(l=10, r=10, t=10, b=90), height=430)
        st.plotly_chart(fig6, use_container_width=True)
        card_close()

# =========================================================
# JOB EXPLORER
# =========================================================
elif st.session_state.page == "Job Explorer":
    st.markdown(
        "<div class='dash-header'><div><p class='dash-title'>Job Explorer</p>"
        "<p class='dash-sub'>Search and export the raw postings</p></div></div>",
        unsafe_allow_html=True,
    )
    search = st.text_input("Search job titles", placeholder="e.g. recruiter, analyst, sales manager")
    result = posts_view.copy()
    if search:
        result = result[result["job_title"].str.contains(search, case=False, na=False)]

    card_open(f"{len(result):,} postings match")
    st.dataframe(
        result[["job_id", "category", "job_title", "skill_count"]].rename(columns={"skill_count": "skills_listed"}),
        use_container_width=True, height=440,
    )
    card_close()

    st.download_button("⬇ Download this result set", data=result.to_csv(index=False), file_name="job_search_results.csv", mime="text/csv")

# =========================================================
# ABOUT
# =========================================================
else:
    st.markdown(
        "<div class='dash-header'><div><p class='dash-title'>About</p>"
        "<p class='dash-sub'>How this dashboard is built</p></div></div>",
        unsafe_allow_html=True,
    )
    card_open("Data pipeline")
    st.markdown(
        """
        Built on a scrape of job postings across five categories — HR, Finance, Sales,
        Business Development and IT. `clean.py` parses the raw `job_skill_set` strings into
        real lists, explodes them, and aggregates counts per category into
        `cleaned_skills_count.csv`, which most of the charts here read from. Job Explorer
        reads the raw file directly so individual postings stay searchable.
        """
    )
    st.code("all_job_post.csv  →  clean.py  →  cleaned_skills_count.csv  →  this dashboard", language="text")
    card_close()
