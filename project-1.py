# app.py
import streamlit as st
import pandas as pd
import numpy as np

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Tennis Analytics Dashboard", layout="wide")

# -------------------------
# Helpers
# -------------------------
def safe_read_csv(path):
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"❌ File not found: {path}")
        return pd.DataFrame()
    except pd.errors.EmptyDataError:
        st.error(f"❌ File is empty: {path}")
        return pd.DataFrame()

@st.cache_data
def load_data():
    competitors = safe_read_csv("Competitors.csv")
    rankings = safe_read_csv("Competitor_Rankings.csv")

    if competitors.empty or rankings.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Normalize column names
    competitors.rename(columns={
        "id": "competitor_id", "competitorId": "competitor_id",
        "name": "name", "country_name": "country",
        "country": "country", "country_code": "country_code",
        "abbr": "abbreviation"}, inplace=True, errors="ignore")

    rankings.rename(columns={
        "id": "competitor_id", "competitorId": "competitor_id",
        "rank": "rank", "points": "points",
        "movement": "movement", "competitions_played": "competitions_played",
        "year": "year", "week": "week", "gender": "gender",
        "type": "type"}, inplace=True, errors="ignore")

    # Convert numerics
    for col in ["rank","points","movement","competitions_played","year","week"]:
        if col in rankings.columns:
            rankings[col] = pd.to_numeric(rankings[col], errors="coerce")

    # Merge
    if "competitor_id" in competitors.columns and "competitor_id" in rankings.columns:
        merged = rankings.merge(competitors, on="competitor_id", how="left")
    else:
        merged = rankings.copy()

    return competitors, rankings, merged

# -------------------------
# Load
# -------------------------
competitors_df, rankings_df, df = load_data()

if df.empty:
    st.title("🏆 Tennis Analytics Dashboard")
    st.warning("No data found. Please generate and place 'Competitors.csv' and 'Competitor_Rankings.csv'.")
    st.stop()

# -------------------------
# Sidebar Filters
# -------------------------
st.sidebar.header("Filters")

# Year filter
if "year" in df.columns and df["year"].notna().any():
    min_year, max_year = int(df["year"].min()), int(df["year"].max())
    if min_year == max_year:
        year_range = (min_year, max_year)
        st.sidebar.info(f"Year: {min_year} (only)")
    else:
        year_range = st.sidebar.slider("Year range", min_year, max_year, (min_year, max_year))
else:
    year_range = None

# Week filter
if "week" in df.columns and df["week"].notna().any():
    min_week, max_week = int(df["week"].min()), int(df["week"].max())
    if min_week == max_week:
        week_range = (min_week, max_week)
        st.sidebar.info(f"Week: {min_week} (only)")
    else:
        week_range = st.sidebar.slider("Week range", min_week, max_week, (min_week, max_week))
else:
    week_range = None

# Gender filter
genders = sorted(df["gender"].dropna().unique()) if "gender" in df.columns else []
gender_sel = st.sidebar.multiselect("Gender", genders, default=genders)

# Country filter
countries = sorted(df["country"].dropna().unique()) if "country" in df.columns else []
country_sel = st.sidebar.multiselect("Country", countries, default=[])

# Rank filter
if "rank" in df.columns and df["rank"].notna().any():
    min_rank, max_rank = int(df["rank"].min()), int(df["rank"].max())
    rank_range = st.sidebar.slider("Rank range", min_rank, max_rank, (min_rank, min(min_rank+20,max_rank)))
else:
    rank_range = None

# Points filter
if "points" in df.columns and df["points"].notna().any():
    min_points, max_points = int(df["points"].min()), int(df["points"].max())
    points_range = st.sidebar.slider("Points range", min_points, max_points, (min_points, max_points))
else:
    points_range = None

# Name search
name_search = st.sidebar.text_input("Search competitor name")

# -------------------------
# Apply Filters
# -------------------------
filtered = df.copy()

if year_range: filtered = filtered[(filtered["year"] >= year_range[0]) & (filtered["year"] <= year_range[1])]
if week_range: filtered = filtered[(filtered["week"] >= week_range[0]) & (filtered["week"] <= week_range[1])]
if gender_sel: filtered = filtered[filtered["gender"].isin(gender_sel)]
if country_sel: filtered = filtered[filtered["country"].isin(country_sel)]
if rank_range: filtered = filtered[(filtered["rank"] >= rank_range[0]) & (filtered["rank"] <= rank_range[1])]
if points_range: filtered = filtered[(filtered["points"] >= points_range[0]) & (filtered["points"] <= points_range[1])]
if name_search: filtered = filtered[filtered["name"].str.contains(name_search, case=False, na=False)]

# -------------------------
# Homepage KPIs
# -------------------------
st.title("🏆 Tennis Analytics Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Total Competitors", df["competitor_id"].nunique())
col2.metric("Countries Represented", df["country"].nunique())
col3.metric("Highest Points", int(df["points"].max()))

st.subheader("📊 Filtered KPIs")
col4, col5, col6 = st.columns(3)
col4.metric("Competitors (filtered)", filtered["competitor_id"].nunique())
col5.metric("Countries (filtered)", filtered["country"].nunique())
col6.metric("Highest Points (filtered)", int(filtered["points"].max()) if not filtered.empty else 0)

st.markdown("---")

# -------------------------
# Search Results
# -------------------------
st.subheader("🔍 Filtered Competitors")
if filtered.empty:
    st.warning("No results match filters.")
else:
    show_cols = [c for c in ["rank","name","country","points","movement","competitions_played","year","week","gender"] if c in filtered.columns]
    st.dataframe(filtered[show_cols].sort_values("rank").reset_index(drop=True))

st.markdown("---")

# -------------------------
# Competitor Details
# -------------------------
st.subheader("📋 Competitor Details")
if not filtered.empty:
    selected = st.selectbox("Select Competitor", sorted(filtered["name"].unique()))
    details = filtered[filtered["name"] == selected].iloc[0]
    st.write(f"**Name:** {details['name']}")
    st.write(f"**Rank:** {details['rank']}")
    st.write(f"**Points:** {details['points']}")
    st.write(f"**Movement:** {details['movement']}")
    st.write(f"**Competitions Played:** {details['competitions_played']}")
    st.write(f"**Country:** {details['country']}")

st.markdown("---")

# -------------------------
# Country Analysis
# -------------------------
st.subheader("🌍 Country Analysis")
if not filtered.empty:
    country_stats = (filtered.groupby("country")
                     .agg(total_competitors=("competitor_id","nunique"),
                          avg_points=("points","mean"))
                     .reset_index()
                     .sort_values("total_competitors",ascending=False))
    st.dataframe(country_stats)

st.markdown("---")

# -------------------------
# Leaderboards
# -------------------------
st.subheader("🏅 Leaderboards")
if not filtered.empty:
    tab1, tab2 = st.tabs(["Top Ranked", "Highest Points"])
    with tab1:
        st.dataframe(filtered.sort_values("rank").head(10)[["rank","name","country","points"]])
    with tab2:
        st.dataframe(filtered.sort_values("points",ascending=False).head(10)[["rank","name","country","points"]])
