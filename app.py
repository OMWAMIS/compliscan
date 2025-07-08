import streamlit as st
import fitz  # PyMuPDF
import docx
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CompliScan: Contract Analyzer", layout="wide")
st.title("🛡️ CompliScan: Contract Analyzer")
st.markdown("Upload contract(s) and an OSH Risk Evaluator to detect compliance, risk, and key schedules.")

col1, col2 = st.columns(2)

with col1:
    contract_files = st.file_uploader("📄 Upload Contract(s)", type=["pdf", "docx"], accept_multiple_files=True)

with col2:
    osh_file = st.file_uploader("📘 Upload OSH Risk Evaluator", type=["pdf", "docx"])

key_schedules = [
    "PRICING", "SCOPE OF WORK", "SLA", "SAFETY OSH", "SUPPLIER CODE OF CONDUCT",
    "DOCUMENT VERSION OSH", "DOCUMENT VERSION CODE OF CONDUCT", "LIQUIDATED DAMAGES",
    "PAYMENT TERMS", "INCOTERMS"
]

def extract_text(file):
    if file.name.endswith(".pdf"):
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return "\n".join([page.get_text() for page in doc])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

def extract_risk_keywords(text):
    risk_levels = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for level in risk_levels:
        pattern = rf"{level}[\s\-:]*([^\n]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            keywords = [kw.strip().lower() for kw in re.split(r"[;,]", match.group(1))]
            risk_levels[level] = keywords
    return risk_levels

def classify_risk(text, risk_keywords):
    text_lower = text.lower()
    for level in ["HIGH", "MEDIUM", "LOW"]:
        for kw in risk_keywords.get(level, []):
            if kw in text_lower:
                return level
    return "Unknown"

def check_schedules(text):
    found = []
    for schedule in key_schedules:
        if schedule.lower() in text.lower():
            found.append(schedule)
    return found

# Main logic
if contract_files and osh_file:
    st.success("✅ Files uploaded. Analyzing...")

    osh_text = extract_text(osh_file)
    risk_keywords = extract_risk_keywords(osh_text)

    st.info("📘 Extracted Risk Keywords:")
    for level, kws in risk_keywords.items():
        st.markdown(f"**{level}**: {', '.join(kws) if kws else 'None found'}")

    results = []

    for file in contract_files:
        contract_text = extract_text(file)
        risk = classify_risk(contract_text, risk_keywords)
        schedules = check_schedules(contract_text)

        results.append({
            "File Name": file.name,
            "Risk Level": risk,
            "Schedules Found": ", ".join(schedules)
        })

        with st.expander(f"📄 {file.name}"):
            st.markdown(f"**Risk Classification:** `{risk}`")
            st.markdown(f"**Schedules Found:** {', '.join(schedules) if schedules else 'None' }")
            st.text_area("📑 Contract Preview", contract_text[:1500], height=200)

    df = pd.DataFrame(results)
    st.subheader("📋 Contract Analysis Summary")
    st.dataframe(df)

    # Download Excel button
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    st.download_button("📥 Download Excel Report", data=buffer.getvalue(), file_name="CompliScan_Results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.warning("⬆️ Please upload both contract(s) and an OSH risk evaluator file to continue.")
