import streamlit as st
import fitz  # PyMuPDF
import docx
import re

# --- App Configuration ---
st.set_page_config(page_title="CompliScan: Contract Analyzer", layout="wide")
st.title("🛡️ CompliScan: Contract Analyzer")
st.markdown("Upload contract(s) and current OSH version to detect compliance, risk, and key schedules.")

# --- File Uploaders ---
col1, col2 = st.columns(2)

with col1:
    contract_files = st.file_uploader("📄 Upload Contract(s)", type=["pdf", "docx"], accept_multiple_files=True)

with col2:
    osh_file = st.file_uploader("📘 Upload Current OSH Reference", type=["pdf", "docx"])

# --- Key Definitions ---
key_schedules = [
    "PRICING", "SCOPE OF WORK", "SLA", "SAFETY OSH", "SUPPLIER CODE OF CONDUCT",
    "DOCUMENT VERSION OSH", "DOCUMENT VERSION CODE OF CONDUCT", "LIQUIDATED DAMAGES",
    "PAYMENT TERMS", "INCOTERMS"
]

risk_keywords = {
    "HIGH": ["working at height", "confined spaces", "electrical", "fiber spl]()
