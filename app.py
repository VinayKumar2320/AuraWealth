import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.append(str(BACKEND))

from app.services.allocation_service import AllocationService
from app.services.mock_data_service import MockDataService

st.set_page_config(page_title="AuraWealth", page_icon="📈", layout="wide")

st.title("AuraWealth")
st.caption("A lightweight Streamlit dashboard for portfolio allocation and stock research insights.")

service = MockDataService()
allocator = AllocationService()

with st.sidebar:
    st.header("Portfolio settings")
    amount = st.slider("Investment amount ($)", min_value=25, max_value=1000, value=250, step=25)
    risk_level = st.selectbox("Risk profile", ["moderate", "conservative", "aggressive"])
    st.markdown("This demo uses mock market data and calculated allocations.")
    generate = st.button("Generate portfolio", use_container_width=True)

if "allocation_result" not in st.session_state or generate:
    recommendations = service.get_daily_recommendations(risk_level)
    allocation_result = allocator.calculate_allocation(amount, recommendations)
    st.session_state["allocation_result"] = allocation_result

allocation_result = st.session_state["allocation_result"]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Investment amount", f"${amount:,.2f}")
with col2:
    st.metric("Total allocated", f"${allocation_result['total_allocated']:,.2f}")
with col3:
    st.metric("Recommended positions", len(allocation_result.get("allocations", [])))

if allocation_result.get("allocations"):
    alloc_df = pd.DataFrame(allocation_result["allocations"])
    display_df = alloc_df[["ticker", "sector", "allocation_pct", "dollar_split", "shares", "price"]].copy()
    display_df = display_df.rename(columns={
        "allocation_pct": "Allocation %",
        "dollar_split": "Dollar split",
        "shares": "Shares",
        "price": "Price",
    })

    st.subheader("Allocation breakdown")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.subheader("Sector diversification")
    sector_df = pd.DataFrame(
        list(allocation_result.get("sector_diversification", {}).items()),
        columns=["Sector", "Allocation %"],
    )
    st.bar_chart(sector_df.set_index("Sector"), use_container_width=True)

    st.subheader("Why these picks")
    for _, row in alloc_df.iterrows():
        with st.expander(f"{row['ticker']} — {row['name']}"):
            st.write(row["why_buy_today"])
            st.write(f"Sentiment score: {row['sentiment_score']}")
            st.write(f"Sector: {row['sector']}")
else:
    st.info("No allocations available yet. Adjust your settings and generate a new portfolio.")
