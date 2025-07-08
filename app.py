# FULL FEATURED: CompliScan Analyzer with PDF, Excel, SQLite, and Risk/Entity Analysis

import streamlit as st
import fitz  # PyMuPDF
import docx
import re
import pandas as pd
import sqlite3
from fpdf import FPDF
import io
import base64

st.set_page_config(page_title="CompliScan: Contract Analyzer", layout="wide")
st.title("🛡️ CompliScan: Contract Analyzer")
st.markdown("Upload contract(s) and current OSH version to detect compliance, risk, and key schedules.")

col1, col2 = st.columns(2)

with col1:
    contract_files = st.file_uploader("\U0001f4c4 Upload Contract(s)", type=["pdf", "docx"], accept_multiple_files=True)

with col2:
    osh_file = st.file_uploader("\U0001f4d8 Upload Current OSH Reference", type=["pdf", "docx"])

# --- Globals ---
key_schedules = [
    "PRICING", "SCOPE OF WORK", "SLA", "SAFETY OSH", "SUPPLIER CODE OF CONDUCT",
    "DOCUMENT VERSION OSH", "DOCUMENT VERSION CODE OF CONDUCT", "LIQUIDATED DAMAGES",
    "PAYMENT TERMS", "INCOTERMS"
]

risk_keywords = {
    "HIGH": ["working at height", "confined spaces", "electrical", "fiber splicing", "explosive", "hot works"],
    "MEDIUM": ["maintenance", "installation", "driving", "repairs", "testing"],
    "LOW": ["cleaning", "administration", "delivery", "inspection"]
}

# --- Functions ---
def extract_text(file):
    if file.name.endswith(".pdf"):
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return "\n".join([page.get_text() for page in doc])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

def find_osh_version(text):
    patterns = [
        r"OSH\s*Version\s*:?\s*([0-9.]+)",
        r"Version\s*:?\s*([0-9.]+).*OSH",
        r"Occupational\s+Safety\s+and\s+Health.*Version\s*:?\s*([0-9.]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Not Found"

def classify_risk(text):
    for level, keywords in risk_keywords.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                return level
    return "Unknown"

def check_schedules(text):
    return [s for s in key_schedules if s.lower() in text.lower()]

def tag_entities(text):
    dates = re.findall(r"\b\d{1,2}\s+\w+\s+\d{4}\b", text)
    parties = re.findall(r"(?i)(between|among)\s+(.*?)\s+(and|&)", text)
    return {
        "dates": dates,
        "parties": [" ".join(p[1:]) for p in parties]
    }

def generate_pdf_report(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="CompliScan Compliance Report", ln=True, align="C")
    for item in data:
        pdf.ln(5)
        pdf.multi_cell(0, 10, f"Contract: {item['name']}\nOSH Version: {item['version']}\nCompliance: {item['compliance']}\nRisk: {item['risk']}\nSchedules: {', '.join(item['schedules'])}\nEntities: {item['entities']}")
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    return pdf_output

def generate_csv(data):
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode()

def save_to_db(data):
    conn = sqlite3.connect("contracts.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS analysis (
        name TEXT, version TEXT, compliance TEXT, risk TEXT, schedules TEXT, entities TEXT
    )''')
    for row in data:
        c.execute("INSERT INTO analysis VALUES (?, ?, ?, ?, ?, ?)", (
            row['name'], row['version'], row['compliance'], row['risk'], ", ".join(row['schedules']), str(row['entities'])
        ))
    conn.commit()
    conn.close()

# --- Main ---
if contract_files and osh_file:
    osh_text = extract_text(osh_file)
    current_osh_version = find_osh_version(osh_text)
    st.info(f"\U0001f4d8 Current OSH Version: `{current_osh_version}`")

    compliant_contracts = []
    non_compliant_contracts = []
    contract_data = []

    for file in contract_files:
        contract_text = extract_text(file)
        contract_version = find_osh_version(contract_text)
        compliance = "Compliant" if contract_version == current_osh_version else "Not Compliant"
        risk = classify_risk(contract_text)
        schedules_found = check_schedules(contract_text)
        entities = tag_entities(contract_text)

        if compliance == "Compliant":
            compliant_contracts.append(file.name)
        else:
            non_compliant_contracts.append(file.name)

        contract_data.append({
            "name": file.name,
            "version": contract_version,
            "compliance": compliance,
            "risk": risk,
            "schedules": schedules_found,
            "entities": entities
        })

        with st.expander(f"\U0001f4c4 {file.name}"):
            st.markdown(f"**OSH Version Detected:** `{contract_version}`")
            st.markdown(f"**Compliance Status:** {compliance}")
            st.markdown(f"**Risk Classification:** `{risk}`")
            st.markdown(f"**Schedules Found:** {', '.join(schedules_found) if schedules_found else 'None'}")
            st.markdown(f"**Entities Detected:** `{entities}`")
            st.text_area("\U0001f4d1 Contract Preview", contract_text[:1000], height=200)

    st.subheader("\U0001f4cb Compliance Summary"
