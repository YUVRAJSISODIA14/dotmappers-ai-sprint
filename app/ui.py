"""
ui.py — Streamlit front-end for the support ticket AI system.

Imports the same functions used by main.py directly, rather than
calling the API over HTTP — same logic, no duplicate code, and no
dependency on the FastAPI server being up at the same time.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
from app.query_engine import answer_question
from app.anomalies import get_all_anomalies

st.set_page_config(page_title="Support Ticket AI System", layout="wide")
st.title("Support Ticket AI System")

# --- Section 1: Ask a question ---
st.header("Ask a question about the tickets")
question = st.text_input("e.g. How many critical tickets are unresolved?")

if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        try:
            answer = answer_question(question)
            st.success(answer)
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# --- Section 2: Anomalies ---
st.header("Detected anomalies")

if st.button("Refresh anomalies"):
    with st.spinner("Scanning for anomalies..."):
        anomalies = get_all_anomalies()
        st.session_state["anomalies"] = anomalies

if "anomalies" in st.session_state:
    anomalies_df = pd.DataFrame(st.session_state["anomalies"])
    st.write(f"Found {len(anomalies_df)} anomalies")
    st.dataframe(anomalies_df, use_container_width=True)
else:
    st.info("Click 'Refresh anomalies' to run the anomaly checks.")