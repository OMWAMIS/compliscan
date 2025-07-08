import streamlit as st
import fitz  # PyMuPDF
import docx
import re
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import base64
import io

st.set_page_config(page_title="CompliScan: Contract Analyzer", layout="wide")
st.title("🛡️ CompliScan: Contract Analyzer")
st.markdown("Upload contract(s) and current OSH version to detect compliance, risk, and key schedules.")

col1, col2 = st.columns(2)

with col1:
    contract_files = st.file_uploader("📄 Upload Contract(s)", type=["pdf", "docx"], accept_multiple_files=True)

with col2:
    osh_file = st.file_uploader("📘 Upload Current OSH Reference", type=["pdf", "docx"])

key_schedules = [
    "PRICING", "SCOPE OF WORK", "SLA", "SAFETY OSH", "SUPPLIER CODE OF CONDUCT",
    "DOCUMENT VERSION OSH", "DOCUMENT VERSION CODE OF CONDUCT",
    "LIQUIDATED DAMAGES", "PAYMENT TERMS", "INCOTERMS"
]

risk_keywords = {
    "HIGH": ["working at height", "confined spaces", "electrical", "fiber splicing", "explosive", "hot works"],
    "MEDIUM": ["maintenance", "installation", "driving", "repairs", "testing"],
    "LOW": ["cleaning", "administration", "delivery", "inspection"]
}

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
        r"OSH\s*Version\s*:?[\s\-]*([0-9.]+)",
        r"Version\s*:?[\s\-]*([0-9.]+).*OSH",
        r"Occupational\s+Safety\s+and\s+Health\s+Schedule.*Version\s*:?[\s\-]*([0-9.]+)"
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
    found = []
    for schedule in key_schedules:
        if schedule.lower() in text.lower():
            found.append(schedule)
    return found

def generate_csv(dataframe):
    return dataframe.to_csv(index=False).encode('utf-8')

def generate_pdf_report(results):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="CompliScan Compliance Report", ln=True, align="C")
    pdf.ln(10)
    for result in results:
        pdf.multi_cell(0, 10, txt=f"Contract: {result['file']}")
        pdf.multi_cell(0, 10, txt=f"  OSH Version Detected: {result['version']}")
        pdf.multi_cell(0, 10, txt=f"  Compliance: {result['compliance']}")
        pdf.multi_cell(0, 10, txt=f"  Risk: {result['risk']}")
        pdf.multi_cell(0, 10, txt=f"  Schedules: {', '.join(result['schedules']) if result['schedules'] else 'None'}")
        pdf.ln(5)
    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

def save_to_database(results):
    conn = sqlite3.connect("compliance.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contracts
                 (timestamp TEXT, filename TEXT, version TEXT, compliance TEXT, risk TEXT, schedules TEXT)''')
    for r in results:
        c.execute("INSERT INTO contracts VALUES (?, ?, ?, ?, ?, ?)", (
            datetime.now().isoformat(),
            r['file'],
            r['version'],
            r['compliance'],
            r['risk'],
            ', '.join(r['schedules'])
        ))
    conn.commit()
    conn.close()

if contract_files and osh_file:
    st.success("✅ Files uploaded. Analyzing...")

    osh_text = extract_text(osh_file)
    current_osh_version = find_osh_version(osh_text)

    st.info(f"📘 Current OSH Version: `{current_osh_version}`")

    results = []
    compliant_contracts = []
    non_compliant_contracts = []

    for file in contract_files:
        contract_text = extract_text(file)
        version = find_osh_version(contract_text)
        compliance = "✅ Compliant" if version == current_osh_version and version != "Not Found" else "❌ Not Compliant"
        risk = classify_risk(contract_text)
        schedules = check_schedules(contract_text)

        if compliance == "✅ Compliant":
            compliant_contracts.append(file.name)
        else:
            non_compliant_contracts.append(file.name)

        result = {
            "file": file.name,
            "version": version,
            "compliance": compliance,
            "risk": risk,
            "schedules": schedules
        }
        results.append(result)

        with st.expander(f"📄 {file.name}"):
            st.markdown(f"**OSH Version Detected:** `{version}`")
            st.markdown(f"**Compliance Status:** {compliance}")
            st.markdown(f"**Risk Classification:** `{risk}`")
            st.markdown(f"**Schedules Found:** {', '.join(schedules) if schedules else 'None'}")
            st.text_area("📑 Contract Preview", contract_text[:1000], height=200)

    df = pd.DataFrame(results)

    st.subheader("📋 Compliance Summary")
    st.success(f"✅ Compliant Contracts: {len(compliant_contracts)}")
    st.error(f"❌ Non-Compliant Contracts: {len(non_compliant_contracts)}")
    if non_compliant_contracts:
        st.markdown("**Non-Compliant List:**")
        for nc in non_compliant_contracts:
            st.markdown(f"- ❌ {nc}")

    st.download_button("⬇️ Download CSV", data=generate_csv(df), file_name="compliance_report.csv", mime="text/csv")

    pdf_bytes = generate_pdf_report(results)
    st.download_button("⬇️ Download PDF Report", data=pdf_bytes, file_name="compliance_report.pdf", mime="application/pdf")

    save_to_database(results)
    st.info("💾 Results saved to SQLite database: `compliance.db`")

else:
    st.warning("⬆️ Please upload contract(s) and OSH reference to start.")
