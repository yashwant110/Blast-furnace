import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Blast Furnace-2 Dashboard",
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: white;
    font-family: Segoe UI, sans-serif;
}
.top-bar {
    height: 10px;
    background-color: #F57C00;
    margin-bottom: 10px;
}
.main-title {
    color: #0D1B2A;
    text-align: center;
    font-weight: 700;
}
.subtitle {
    text-align: center;
    color: #0D1B2A;
    margin-top: -8px;
}
.title-line {
    width: 360px;
    height: 3px;
    background-color: #F57C00;
    margin: 8px auto 18px auto;
}
.kpi-card {
    background: linear-gradient(135deg, #0D1B2A, #1B2A41);
    color: white;
    padding: 22px;
    border-radius: 10px;
    text-align: center;
    border-bottom: 6px solid #F57C00;
}
.kpi-value {
    font-size: 32px;
    font-weight: bold;
}
.net-highlight {
    color: #F57C00;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<div class='top-bar'></div>", unsafe_allow_html=True)

h1, h2, h3 = st.columns([1, 6, 1])
with h1:
    st.image("assets/jindal_logo.png", width=110)
with h2:
    st.markdown("<h2 class='main-title'>Blast Furnace-2 | Torpedo Dispatch Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<div class='title-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Hot Metal Production Monitoring</div>", unsafe_allow_html=True)

st.markdown("---")

# ---------------- DATA LOADER ----------------
@st.cache_data
def load_data():
    df = pd.read_excel("data/ladle_weight_bf2.xlsx")
    df.columns = df.columns.str.strip().str.upper()

    def find_col(key):
        for c in df.columns:
            if key in c:
                return c
        return None

    cols = {
        "Date": find_col("DATE"),
        "Cast ID": find_col("CAST"),
        "Torpedo No": find_col("TORPEDO"),
        "Gross (t)": find_col("GROSS"),
        "Tare (t)": find_col("TARE"),
        "Net (t)": find_col("NET")
    }

    clean = pd.DataFrame()
    for k, v in cols.items():
        if v is None:
            st.error(f"Missing column in Excel: {k}")
            st.stop()
        clean[k] = df[v]

    clean["Date"] = pd.to_datetime(clean["Date"], errors="coerce")

    for col in ["Gross (t)", "Tare (t)", "Net (t)"]:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")

    clean["Torpedo No"] = clean["Torpedo No"].astype("Int64").astype(str)

    return clean.dropna(subset=["Date"])

df = load_data()

# ---------------- DATE SELECTION ----------------
st.subheader("Date Selection")

mode = st.radio(
    "View Mode",
    ["Single Day", "Date Range"],
    horizontal=True
)

if mode == "Single Day":
    selected_date = st.date_input("Select Date", df["Date"].min())
    start_date = pd.to_datetime(selected_date)
    end_date = start_date
else:
    date_range = st.date_input(
        "Select Date Range",
        [df["Date"].min(), df["Date"].max()]
    )
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

# ---------------- FILTERS ----------------
f1, f2 = st.columns(2)

with f1:
    torpedo_filter = st.multiselect(
        "Torpedo No",
        sorted(df["Torpedo No"].unique())
    )

with f2:
    cast_search = st.text_input("Cast ID")

filtered = df[
    (df["Date"] >= start_date) &
    (df["Date"] <= end_date)
]

if filtered.empty:
    st.warning("No data available for the selected date(s)")
    st.stop()

if torpedo_filter:
    filtered = filtered[filtered["Torpedo No"].isin(torpedo_filter)]

if cast_search:
    filtered = filtered[
        filtered["Cast ID"].astype(str).str.contains(cast_search, case=False)
    ]

# ---------------- RESET LEFT INDEX PER DAY ----------------
filtered = (
    filtered
    .sort_values("Date")
    .groupby(filtered["Date"].dt.date, group_keys=False)
    .apply(lambda x: x.reset_index(drop=True))
)

filtered.index = filtered.index + 1

# ---------------- KPIs ----------------
k1, k2, k3, k4 = st.columns(4)

k1.markdown(f"<div class='kpi-card'>Total Casts<div class='kpi-value'>{filtered['Cast ID'].nunique()}</div></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='kpi-card'>Torpedos Used<div class='kpi-value'>{filtered['Torpedo No'].nunique()}</div></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='kpi-card'>Total Net Hot Metal<div class='kpi-value net-highlight'>{filtered['Net (t)'].sum():,.1f} t</div></div>", unsafe_allow_html=True)
k4.markdown(f"<div class='kpi-card'>Avg Net / Cast<div class='kpi-value'>{filtered['Net (t)'].mean():.1f} t</div></div>", unsafe_allow_html=True)

# ---------------- TABLE (STABLE) ----------------
st.markdown("### Torpedo Dispatch Details")

display_df = filtered.copy()
display_df["Date"] = display_df["Date"].dt.date

display_df = display_df[
    ["Date", "Cast ID", "Torpedo No", "Gross (t)", "Tare (t)", "Net (t)"]
]

st.dataframe(display_df, use_container_width=True)

# ---------------- CHARTS ----------------
c1, c2, c3 = st.columns(3)

c1.plotly_chart(px.bar(filtered, x="Date", y="Net (t)", title="Daily Net Hot Metal (t)",
                       color_discrete_sequence=["#F57C00"]), use_container_width=True)

c2.plotly_chart(px.bar(filtered, x="Torpedo No", y="Net (t)", title="Torpedo vs Net Metal (t)",
                       color_discrete_sequence=["#F57C00"]), use_container_width=True)

stack_df = filtered.groupby("Torpedo No", as_index=False)[
    ["Gross (t)", "Tare (t)", "Net (t)"]
].sum()

c3.plotly_chart(px.bar(stack_df, x="Torpedo No",
                       y=["Gross (t)", "Tare (t)", "Net (t)"],
                       title="Gross, Tare & Net Weight (t)",
                       barmode="stack",
                       color_discrete_sequence=["#F57C00", "#2E3440", "#D32F2F"]),
                use_container_width=True)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("<center>© Blast Furnace-2 | Jindal Steel</center>", unsafe_allow_html=True)
