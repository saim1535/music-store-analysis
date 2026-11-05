import pandas as pd
import plotly.express as px
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Music Store Analysis Dashboard", page_icon="🎵", layout="wide"
)

st.title("🎵 Music Store Analysis Report & Dashboard")
st.markdown(
    "Explore overall revenue trends, customer behaviors, genre performance, and"
    " key store metrics interactively."
)


# --- LOAD DATA FROM CSV FILES (Cached for performance) ---
@st.cache_data
def load_data():
  # Ye files aapke GitHub repo mein honi chahiyein
  invoice = pd.read_csv("invoice.csv")
  invoice_line = pd.read_csv("invoice_line.csv")
  track = pd.read_csv("track.csv")
  genre = pd.read_csv("genre.csv")
  customer = pd.read_csv("customer.csv")

  # Date column ko datetime mein convert karna
  invoice["invoice_date"] = pd.to_datetime(invoice["invoice_date"])
  return invoice, invoice_line, track, genre, customer


try:
  invoice_df, invoice_line_df, track_df, genre_df, customer_df = load_data()
except Exception as e:
  st.error(
      "Data files load karne mein masla hai! Please ensure invoice.csv,"
      " invoice_line.csv, track.csv, genre.csv, aur customer.csv GitHub par"
      f" uploaded hain. Details: {e}"
  )
  st.stop()


# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Control Panel & Filters")

min_d = invoice_df["invoice_date"].dt.date.min()
max_d = invoice_df["invoice_date"].dt.date.max()

# Date Range Filter
date_range = st.sidebar.date_input(
    "Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d
)

if len(date_range) != 2:
  st.warning("Please select both start and end date.")
  st.stop()

start_date, end_date = date_range

# Time Granularity Selection
granularity = st.sidebar.selectbox(
    "Time Granularity", ["Monthly", "Quarterly", "Yearly"]
)

freq_map = {"Monthly": "MS", "Quarterly": "QS", "Yearly": "YS"}
freq_val = freq_map[granularity]

# Country Filter
all_countries = sorted(
    invoice_df["billing_country"].dropna().unique().tolist()
)
selected_countries = st.sidebar.multiselect(
    "Select Country/Countries", options=all_countries, default=all_countries
)

if not selected_countries:
  st.warning("Please select at least one country to view data.")
  st.stop()

# --- FILTER DATAFRAME ---
mask = (
    (invoice_df["invoice_date"].dt.date >= start_date)
    & (invoice_df["invoice_date"].dt.date <= end_date)
    & (invoice_df["billing_country"].isin(selected_countries))
)
filtered_invoice = invoice_df[mask]


# --- 1. KEY PERFORMANCE INDICATORS (KPIs) ---
total_rev = filtered_invoice["total"].sum() if not filtered_invoice.empty else 0
total_inv = (
    filtered_invoice["invoice_id"].nunique()
    if not filtered_invoice.empty
    else 0
)
total_cust = (
    filtered_invoice["customer_id"].nunique()
    if not filtered_invoice.empty
    else 0
)
avg_ord = filtered_invoice["total"].mean() if not filtered_invoice.empty else 0

st.markdown("---")
st.subheader("📊 Executive Summary / KPIs")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Revenue", f"${total_rev:,.2f}")
col2.metric("🧾 Total Invoices", f"{total_inv:,}")
col3.metric("👥 Active Customers", f"{total_cust:,}")
col4.metric("🛒 Avg Order Value (AOV)", f"${avg_ord:,.2f}")

st.markdown("---")


# --- 2. REVENUE TREND OVER TIME ---
st.subheader(f"📈 Revenue Trend ({granularity})")

if not filtered_invoice.empty:
  trend_df = (
      filtered_invoice.set_index("invoice_date")
      .groupby(pd.Grouper(freq=freq_val))["total"]
      .sum()
      .reset_index()
  )
  trend_df.columns = ["period", "revenue"]
  trend_df["period"] = trend_df["period"].dt.date

  fig_trend = px.area(
      trend_df,
      x="period",
      y="revenue",
      markers=True,
      labels={"period": "Time Period", "revenue": "Revenue ($)"},
      title=f"Revenue Over Time ({granularity})",
  )
  fig_trend.update_layout(
      xaxis_title="Period", yaxis_title="Revenue ($)", hovermode="x unified"
  )
  st.plotly_chart(fig_trend, use_container_width=True)
else:
  st.info("No data available for the selected date range and country filters.")


# --- 3. TWO COLUMNS FOR ADVANCED INSIGHTS ---
col_left, col_right = st.columns(2)

with col_left:
  st.subheader("🌍 Top Countries by Revenue")
  if not filtered_invoice.empty:
    country_df = (
        filtered_invoice.groupby("billing_country")["total"]
        .sum()
        .reset_index()
    )
    country_df.columns = ["country", "revenue"]
    country_df = country_df.sort_values(by="revenue", ascending=False).head(10)

    fig_country = px.bar(
        country_df,
        x="revenue",
        y="country",
        orientation="h",
        text_auto=".2s",
        labels={"revenue": "Revenue ($)", "country": "Country"},
        color="revenue",
        color_continuous_scale="Viridis",
    )
    fig_country.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_country, use_container_width=True)

with col_right:
  st.subheader("🎸 Top Genres by Sales Quantity")
  if not filtered_invoice.empty:
    merged_il = invoice_line_df[
        invoice_line_df["invoice_id"].isin(filtered_invoice["invoice_id"])
    ]
    t_g = track_df.merge(genre_df, on="genre_id", suffixes=("_track", "_genre"))
    il_tg = merged_il.merge(t_g, on="track_id")
    genre_df_agg = (
        il_tg.groupby("name_genre")["quantity"].sum().reset_index()
    )
    genre_df_agg.columns = ["genre", "total_sold"]
    genre_df_agg = genre_df_agg.sort_values(
        by="total_sold", ascending=False
    ).head(10)

    fig_genre = px.pie(
        genre_df_agg,
        names="genre",
        values="total_sold",
        hole=0.4,
        title="Top Music Genres Distribution",
    )
    st.plotly_chart(fig_genre, use_container_width=True)

st.markdown("---")


# --- 4. TOP CUSTOMERS LEADERBOARD ---
st.subheader("🏆 Top Customers Leaderboard")
if not filtered_invoice.empty:
  cust_agg = (
      filtered_invoice.groupby("customer_id")
      .agg(total_orders=("invoice_id", "count"), total_spent=("total", "sum"))
      .reset_index()
  )
  cust_merged = cust_agg.merge(customer_df, on="customer_id")
  cust_merged["customer_name"] = (
      cust_merged["first_name"].fillna("")
      + " "
      + cust_merged["last_name"].fillna("")
  )
  top_cust_df = (
      cust_merged[
          [
              "customer_id",
              "customer_name",
              "country",
              "total_orders",
              "total_spent",
          ]
      ]
      .sort_values(by="total_spent", ascending=False)
      .head(10)
  )
  st.dataframe(top_cust_df, use_container_width=True)