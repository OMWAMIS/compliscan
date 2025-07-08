import streamlit as st
import fitz  # PyMuPDF for PDF
import docx
import re

# Configure page
st.set_page_config(page_title="CompliScan: Contract Analyzer", layout="wide")
st.title("🛡️ CompliScan: Contract Analyzer")
st.markdown("Upload contract(s) and current OSH version to detect compliance, risk, and key schedules.")

# Layout columns for upload
col1, col2 = st.columns(2)
with col1:
    contract_files = st.file_uploader("📄 Upload Contract(s)", type=["pdf", "docx"], accept_multiple_files=True)
with col2:
    osh_file = st.file_uploader("📘 Upload Current OSH Reference", type=["pdf", "docx"])

# Key clauses to check
key_schedules = [
    "PRICING", "SCOPE OF WORK", "SLA", "SAFETY OSH", "SUPPLIER CODE OF CONDUCT",
    "DOCUMENT VERSION OSH", "DOCUMENT VERSION CODE OF CONDUCT",
    "LIQUIDATED DAMAGES", "PAYMENT TERMS", "INCOTERMS"
]

# Risk classification keywords
risk_keywords = {
    "HIGH": ["working at height", "confined spaces", "electrical", "fiber splicing", "explosive", "hot works"],
    "MEDIUM": ["maintenance", "installation", "driving", "repairs", "testing"],
    "LOW": ["cleaning", "administration", "delivery", "inspection"]
}

# Extract text from PDF or DOCX
def extract_text(file):
    if file.name.endswith(".pdf"):
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return "\n".join([page.get_text() for page in doc])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

# Detect OSH version string
def find_osh_version(text):
    patterns = [
        r"OSH\s*Version\s*:?[\s\-]*([0-9.]+)",
        r"Version\s*:?[\s\-]*([0-9.]()
