import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="EpiTrack — COVID-19 Dashboard", page_icon="🦠", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: #0a0e1a; }
[data-testid="stSidebar"] { background: #0f1320 !important; }
.kpi { background: #0f1320; border: 1px solid #1e2a40; border-radius: 12px; padding: 1.2rem 1.5rem; }
.kpi-label { font-size: 0.72rem; color: #6b7a99; text-transform: uppercase; letter-spacing: 0.8px; }
.kpi-value { font-size: 1.8rem; font-weight: 700; color: #e8edf5; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
    df = pd.read_csv(url)
    df = df.drop(columns=["Province/State", "Lat", "Long"])
    df = df.groupby("Country/Region").sum().reset_index()
    df_melted = df.melt(id_vars=["Country/Region"], var_name="Date", value_name="Cases")
    df_melted["Date"] = pd.to_datetime(df_melted["Date"])
    return df_melted

with st.spinner("Loading COVID-19 data..."):
    df = load_data()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🦠 EpiTrack")
    st.markdown("---")
    countries = sorted(df["Country/Region"].unique().tolist())
    selected_countries = st.multiselect("Select Countries", countries, default=["India", "US", "Brazil", "United Kingdom"])
    if not selected_countries:
        selected_countries = ["India"]
    st.markdown("---")
    date_range = st.date_input("Date Range", [df["Date"].min(), df["Date"].max()])
    st.markdown("---")
    forecast_days = st.slider("Forecast Days", 7, 60, 30)

# ── Filter ────────────────────────────────────────────────────
filt = df[
    (df["Country/Region"].isin(selected_countries)) &
    (df["Date"] >= pd.to_datetime(date_range[0])) &
    (df["Date"] <= pd.to_datetime(date_range[1]))
]

# ── Hero ──────────────────────────────────────────────────────
st.markdown("## 🦠 EpiTrack — COVID-19 Epidemic Dashboard")
st.markdown("Real-time outbreak tracking, trend analysis & spread prediction")
st.markdown("---")

# ── KPIs ──────────────────────────────────────────────────────
total_cases = filt.groupby("Country/Region")["Cases"].max().sum()
latest_date = filt["Date"].max()
top_country = filt.groupby("Country/Region")["Cases"].max().idxmax()
top_cases   = filt.groupby("Country/Region")["Cases"].max().max()

col1, col2, col3, col4 = st.columns(4)
col1.metric("🌍 Countries Tracked", len(selected_countries))
col2.metric("📅 Latest Date", latest_date.strftime("%d %b %Y"))
col3.metric("📊 Total Cases", f"{total_cases:,.0f}")
col4.metric("🔴 Highest Cases", f"{top_country}: {top_cases:,.0f}")

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Trend Analysis", "🗺️ Risk Map", "🔮 Forecast", "📊 Comparison"])

# ── TAB 1 — Trend ─────────────────────────────────────────────
with tab1:
    st.markdown("### Daily Case Trends")
    fig_trend = px.line(
        filt, x="Date", y="Cases", color="Country/Region",
        title="Cumulative COVID-19 Cases Over Time",
        template="plotly_dark",
    )
    fig_trend.update_layout(
        paper_bgcolor="#0f1320", plot_bgcolor="#0a0e1a",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=400,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Daily new cases
    st.markdown("### Daily New Cases")
    daily_list = []
    for country in selected_countries:
        c_df = filt[filt["Country/Region"] == country].sort_values("Date").copy()
        c_df["New Cases"] = c_df["Cases"].diff().fillna(0).clip(lower=0)
        daily_list.append(c_df)
    daily_df = pd.concat(daily_list)

    fig_daily = px.bar(
        daily_df, x="Date", y="New Cases", color="Country/Region",
        title="Daily New Cases", template="plotly_dark", barmode="group",
    )
    fig_daily.update_layout(
        paper_bgcolor="#0f1320", plot_bgcolor="#0a0e1a", height=350,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_daily, use_container_width=True)

# ── TAB 2 — Risk Map ──────────────────────────────────────────
with tab2:
    st.markdown("### 🗺️ Global Risk Map — Total Cases by Country")
    latest = df[df["Date"] == df["Date"].max()].copy()
    latest.columns = ["Country", "Date", "Cases"]

    fig_map = px.choropleth(
        latest, locations="Country", locationmode="country names",
        color="Cases", hover_name="Country",
        color_continuous_scale=["#0a0e1a", "#f6ad55", "#fc8181"],
        title="COVID-19 Case Density — Global Risk Map",
        template="plotly_dark",
    )
    fig_map.update_layout(
        paper_bgcolor="#0f1320", geo=dict(bgcolor="#0a0e1a"),
        height=500,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Top 10 countries
    st.markdown("### Top 10 Highest Case Countries")
    top10 = latest.nlargest(10, "Cases")
    fig_top = px.bar(
        top10, x="Cases", y="Country", orientation="h",
        color="Cases", color_continuous_scale=["#63b3ed", "#fc8181"],
        template="plotly_dark",
    )
    fig_top.update_layout(paper_bgcolor="#0f1320", plot_bgcolor="#0a0e1a", height=350)
    st.plotly_chart(fig_top, use_container_width=True)

# ── TAB 3 — Forecast ──────────────────────────────────────────
with tab3:
    st.markdown("### 🔮 Outbreak Forecast — Next {} Days".format(forecast_days))
    forecast_country = st.selectbox("Select Country for Forecast", selected_countries)

    c_df = filt[filt["Country/Region"] == forecast_country].sort_values("Date").copy()
    c_df = c_df.set_index("Date")["Cases"]

    # Simple linear regression forecast
    X = np.arange(len(c_df)).reshape(-1, 1)
    y = c_df.values
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    model = LinearRegression()
    model.fit(X_poly, y)

    future_X = np.arange(len(c_df), len(c_df) + forecast_days).reshape(-1, 1)
    future_X_poly = poly.transform(future_X)
    forecast_vals = model.predict(future_X_poly).clip(min=0)

    future_dates = pd.date_range(c_df.index[-1] + timedelta(days=1), periods=forecast_days)

    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(
        x=c_df.index, y=c_df.values, name="Actual", line=dict(color="#63b3ed", width=2)
    ))
    fig_forecast.add_trace(go.Scatter(
        x=future_dates, y=forecast_vals, name="Forecast",
        line=dict(color="#f6ad55", width=2, dash="dash")
    ))
    fig_forecast.update_layout(
        title=f"{forecast_country} — {forecast_days}-Day Forecast",
        paper_bgcolor="#0f1320", plot_bgcolor="#0a0e1a",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=400, template="plotly_dark",
        xaxis=dict(color="#c8d4e8"), yaxis=dict(color="#c8d4e8"),
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

    predicted_final = int(forecast_vals[-1])
    current_cases   = int(c_df.values[-1])
    growth = ((predicted_final - current_cases) / current_cases * 100) if current_cases > 0 else 0
    col1, col2 = st.columns(2)
    col1.metric("Current Cases", f"{current_cases:,}")
    col2.metric(f"Predicted in {forecast_days} days", f"{predicted_final:,}", f"+{growth:.1f}%")

# ── TAB 4 — Comparison ────────────────────────────────────────
with tab4:
    st.markdown("### 📊 Country Comparison")
    latest_filt = filt[filt["Date"] == filt["Date"].max()]
    fig_comp = px.bar(
        latest_filt.sort_values("Cases", ascending=False),
        x="Country/Region", y="Cases", color="Country/Region",
        template="plotly_dark", title="Total Cases Comparison",
        text="Cases",
    )
    fig_comp.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_comp.update_layout(
        paper_bgcolor="#0f1320", plot_bgcolor="#0a0e1a",
        showlegend=False, height=400,
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Growth rate
    st.markdown("### 7-Day Growth Rate")
    growth_list = []
    for country in selected_countries:
        c_data = filt[filt["Country/Region"] == country].sort_values("Date")
        if len(c_data) >= 7:
            last7  = c_data.iloc[-1]["Cases"]
            prev7  = c_data.iloc[-8]["Cases"]
            rate   = ((last7 - prev7) / prev7 * 100) if prev7 > 0 else 0
            growth_list.append({"Country": country, "7-Day Growth %": round(rate, 2)})
    if growth_list:
        growth_df = pd.DataFrame(growth_list)
        fig_growth = px.bar(
            growth_df.sort_values("7-Day Growth %", ascending=False),
            x="Country", y="7-Day Growth %", color="7-Day Growth %",
            color_continuous_scale=["#68d391", "#f6ad55", "#fc8181"],
            template="plotly_dark", title="7-Day Case Growth Rate (%)",
        )
        fig_growth.update_layout(paper_bgcolor="#0f1320", plot_bgcolor="#0a0e1a", height=350)
        st.plotly_chart(fig_growth, use_container_width=True)

st.markdown("---")
st.markdown("<div style='text-align:center;color:#4a5568;font-size:0.8rem'>EpiTrack Dashboard · Data: Johns Hopkins CSSE · Built with Streamlit & Plotly</div>", unsafe_allow_html=True)