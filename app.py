import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Blast Furnace–2 Dashboard",
    layout="wide"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
    .main {
        background-color: white;
    }
    h1, h2, h3 {
        color: #0D1B2A;
    }
    .subtitle {
        color: #F57C00;
        margin-top: -10px;
    }
    .kpi-card {
        background-color: #0D1B2A;
        padding: 18px;
        border-radius: 10px;
        color: white;
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
col1, col2 = st.columns([1, 6])

with col1:
    st.image("assets/jindal_logo.png", width=120)

with col2:
    st.markdown(
        "<h1>Blast Furnace–2 | Torpedo Dispatch Dashboard</h1>"
        "<div class='subtitle'>Hot Metal Production Monitoring</div>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ---------------- LOAD DATA (ROBUST) ----------------
@st.cache_data
def load_data():
    df = pd.read_excel("data/ladle_weight_bf2.xlsx")

    # Clean column names
    df.columns = df.columns.str.strip().str.upper()

    # Flexible renaming (handles messy plant data)
    rename_map = {
        "DATE": "Date",
        "CAST ID": "Cast ID",
        "CASTID": "Cast ID",
        "TORPEDO NO": "Torpedo No",
        "TORPEDO NO.": "Torpedo No",
        "GROSS (TONNES)": "Gross (t)",
        "GROSS(TONNES)": "Gross (t)",
        "TARE (TONNES)": "Tare (t)",
        "TARE(TONNES)": "Tare (t)",
        "NET (TONNES)": "Net (t)",
        "NET(TONNES)": "Net (t)"
    }

    df = df.rename(columns=rename_map)

    # Convert Date safely
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Keep only required columns
    required_cols = ["Date", "Cast ID", "Torpedo No", "Gross (t)", "Tare (t)", "Net (t)"]
    df = df[required_cols]

    return df.dropna(subset=["Date"])

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

filtered_df = df.copy()

if date_range:
    filtered_df = filtered_df[
        (filtered_df["Date"] >= pd.to_datetime(date_range[0])) &
        (filtered_df["Date"] <= pd.to_datetime(date_range[1]))
    ]

if torpedo_filter:
    filtered_df = filtered_df[filtered_df["Torpedo No"].isin(torpedo_filter)]

if cast_search:
    filtered_df = filtered_df[
        filtered_df["Cast ID"].astype(str).str.contains(cast_search, case=False)
    ]

# ---------------- KPI CARDS ----------------
st.markdown("### Key Metrics")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"<div class='kpi-card'>Total Casts"
        f"<div class='kpi-value'>{filtered_df['Cast ID'].nunique()}</div></div>",
        unsafe_allow_html=True
    )

with k2:
    st.markdown(
        f"<div class='kpi-card'>Torpedos Used"
        f"<div class='kpi-value'>{filtered_df['Torpedo No'].nunique()}</div></div>",
        unsafe_allow_html=True
    )

with k3:
    st.markdown(
        f"<div class='kpi-card'>Total Net Metal (t)"
        f"<div class='kpi-value net-red'>{filtered_df['Net (t)'].sum():.2f}</div></div>",
        unsafe_allow_html=True
    )

with k4:
    avg_net = filtered_df["Net (t)"].mean()
    st.markdown(
        f"<div class='kpi-card'>Avg Net / Cast (t)"
        f"<div class='kpi-value'>{avg_net:.2f}</div></div>",
        unsafe_allow_html=True
    )

# ---------------- TABLE ----------------
st.markdown("### Torpedo Dispatch Details")

styled_df = (
    filtered_df.sort_values("Date")
    .style.format({
        "Gross (t)": "{:.2f}",
        "Tare (t)": "{:.2f}",
        "Net (t)": "{:.2f}"
    })
    .applymap(
        lambda x: "color:#D32F2F; font-weight:bold;",
        subset=["Net (t)"]
    )
)

st.dataframe(styled_df, use_container_width=True)

# ---------------- CHARTS ----------------
st.markdown("### Production Analysis")

c1, c2 = st.columns(2)

with c1:
    fig1 = px.bar(
        filtered_df,
        x="Date",
        y="Net (t)",
        title="Net Hot Metal by Date",
        color_discrete_sequence=["#D32F2F"]
    )
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    fig2 = px.bar(
        filtered_df,
        x="Torpedo No",
        y="Net (t)",
        title="Net Hot Metal by Torpedo",
        color_discrete_sequence=["#F57C00"]
    )
    st.plotly_chart(fig2, use_container_width=True)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    "<center>© Blast Furnace–2 | Jindal Steel</center>",
    unsafe_allow_html=True
)
