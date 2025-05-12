import os
import sys
# Ensure project root is on PYTHONPATH for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import streamlit as st
from sqlalchemy.orm import sessionmaker
from app.db import engine
from app.models import SummaryMetrics

# Set page configuration
st.set_page_config(
    page_title="MeetMate Metrics Dashboard",
    layout="wide"
)

st.title("📊 MeetMate Cost & Token Usage Dashboard")

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Query all metrics
metrics = session.query(SummaryMetrics).all()

# Transform to DataFrame
data = []
for m in metrics:
    data.append({
        "date": m.created_at.date(),
        "prompt_tokens": m.prompt_tokens,
        "completion_tokens": m.completion_tokens,
        "total_tokens": m.total_tokens,
        "cost": m.cost,
    })
df = pd.DataFrame(data)

if df.empty:
    st.warning("No metrics data available. Run some summarizations first!")
else:
    # Group by date
    df_grouped = df.groupby("date").sum().reset_index()

    # Display daily cost
    st.subheader("Daily Cost")
    cost_chart = df_grouped.set_index("date")["cost"]
    st.line_chart(cost_chart)

    # Display token usage
    st.subheader("Daily Token Usage")
    token_chart = df_grouped.set_index("date")[['prompt_tokens', 'completion_tokens', 'total_tokens']]
    st.bar_chart(token_chart)

    # Show raw table
    st.subheader("Raw Metrics Data")
    st.dataframe(df_grouped)

session.close()
