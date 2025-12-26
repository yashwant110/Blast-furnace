import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Blast Furnace–2 Dashboard",
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
    .main { background-color: white; }
    h1 { color: #0D1B2A; }
    .subtitle { color: #F57C00; }
    .kpi {
        background-color: #0D1B2A;
        color: white;
        padding: 18px;
        border-radius: 10px;
        text-align: center;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: bold;
    }
    .net-red {
        color: #D32F2F;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
c1, c2 = st.columns([1, 6])

with c1:
    st.image("assets/jindal_logo.png", width=120)

with c2:
    st.markdown("""
    <h1>Blast Furnace–2 | Torpedo Dispatch Dashboard</h1>
    <div class="subtitle">Hot Metal Production Monitoring</div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------------- DATA LOADER (BULLETPROOF) ----------------
@st.cache_data
def load_data():
    df = pd.read_excel("data/ladle_weight_bf2.xlsx")

    # Normalize column names
    df.columns = df.columns.str.strip().str.upper()

    def find_col(keyword):
        for col in df.columns:
            if keyword in col:
                return col
        return None

    date_col = find_col("DATE")
    cast_col = find_col("CAST")
    torpedo_col = find_col("TORPEDO")
    gross_col = find_col("GROSS")
    tare_col = find_col("TARE")
    net_col = find_col("NET")

    required = {
        "Date": date_col,
        "Cast ID": cast_col,
        "Torpedo No": torpedo_col,
        "Gross (t)": gross_col,
        "Tare (t)": tare_col,
        "Net (t)": net_col
    }

    missing = [k for k, v in required.items() if v is None]
    if missing:
        st.error(f"Missing columns in Excel: {missing}")
        st.stop()

    clean_df = pd.DataFrame()
    for new, old in required.items():
        clean_df[new] = df[old]

    clean_df["Date"] = pd.to_datetime(clean_df["Date"], errors="coerce")

    return clean_df.dropna(subset=["Date"])

df = load_data()

# ---------------- FILTERS ----------------
st.subheader("Filters")

f1, f2, f3 = st.columns(3)

with f1:
    date_range = st.date_input(
        "Date range",
        [df["Date"].min(), df["Date"].max()]
    )

with f2:
    torpedo_filter = st.multiselect(
        "Torpedo No",
        sorted(df["Torpedo No"].dropna().unique())
    )

with f3:
    cast_search = st.text_input("Cast ID")

filtered = df.copy()

filtered = filtered[
    (filtered["Date"] >= pd.to_datetime(date_range[0])) &
    (filtered["Date"] <= pd.to_datetime(date_range[1]))
]

if torpedo_filter:
    filtered = filtered[filtered["Torpedo No"].isin(torpedo_filter)]

if cast_search:
    filtered = filtered[
        filtered["Cast ID"].astype(str).str.contains(cast_search, case=False)
    ]

# ---------------- KPIs ----------------
st.markdown("### Key Metrics")

k1, k2, k3, k4 = st.columns(4)

k1.markdown(f"<div class='kpi'>Total Casts<div class='kpi-value'>{filtered['Cast ID'].nunique()}</div></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='kpi'>Torpedos Used<div class='kpi-value'>{filtered['Torpedo No'].nunique()}</div></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='kpi'>Total Net Metal<div class='kpi-value net-red'>{filtered['Net (t)'].sum():.2f}</div></div>", unsafe_allow_html=True)
k4.markdown(f"<div class='kpi'>Avg Net / Cast<div class='kpi-value'>{filtered['Net (t)'].mean():.2f}</div></div>", unsafe_allow_html=True)

# ---------------- TABLE ----------------
st.markdown("### Torpedo Dispatch Details")

styled = filtered.sort_values("Date").style.applymap(
    lambda x: "color:#D32F2F; font-weight:bold;",
    subset=["Net (t)"]
)

st.dataframe(styled, use_container_width=True)

# ---------------- CHARTS ----------------
st.markdown("### Production Analysis")

c1, c2 = st.columns(2)

c1.plotly_chart(
    px.bar(filtered, x="Date", y="Net (t)", title="Net Hot Metal by Date",
           color_discrete_sequence=["#D32F2F"]),
    use_container_width=True
)

c2.plotly_chart(
    px.bar(filtered, x="Torpedo No", y="Net (t)", title="Net Hot Metal by Torpedo",
           color_discrete_sequence=["#F57C00"]),
    use_container_width=True
)

st.markdown("---")
st.markdown("<center>© Blast Furnace–2 | Jindal Steel</center>", unsafe_allow_html=True)
