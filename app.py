import streamlit as st
import fitz  # PyMuPDF
import docx
import re

st.set_page_config(page_title="CompliScan: Contract Analyzer", layout="wide")
st.title("🛡️ CompliScan: Contract Analyzer")
st.markdown("Upload contract(s) and current OSH version to detect compliance, risk, and key schedules.")

col1, col2 = st.columns(2)

with col1:
    contract_files = st.file_uploader("📄 Upload Contract(s)", type=["pdf", "docx"], accept_multiple_files=True)

with col2:
    osh_file = st.file_uploader("📘 Upload Current OSH Reference", type=["pdf", "docx"])

# -------------------- CONSTANTS --------------------

# Key schedules to detect
key_schedules = [
    "PRICING", "SCOPE OF WORK", "SLA", "SAFETY OSH", "SUPPLIER CODE OF CONDUCT",
    "DOCUMENT VERSION OSH", "DOCUMENT VERSION CODE OF CONDUCT", "LIQUIDATED DAMAGES",
    "PAYMENT TERMS", "INCOTERMS"
]

# Risk levels
risk_keywords = {
    "HIGH": ["working at height", "confined spaces", "electrical", "fiber splicing", "explosive", "hot works"],
    "MEDIUM": ["maintenance", "installation", "driving", "repairs", "testing"],
    "LOW": ["cleaning", "administration", "delivery", "inspection"]
}

# -------------------- FUNCTIONS --------------------

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
        r"OSH\s*Version\s*[:\-]?\s*([0-9.]+)",
        r"Version\s*[:\-]?\s*([0-9.]+).*OSH",
        r"Occupational\s+Safety\s+and\s+Health\s+Schedule.*Version\s*[:\-]?\s*([0-9.]+)"
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

# -------------------- MAIN APP LOGIC --------------------

if contract_files and osh_file:
    st.success("✅ Files uploaded. Analyzing...")

    osh_text = extract_text(osh_file)
    current_osh_version = find_osh_version(osh_text)
    st.info(f"📘 Current OSH Version: `{current_osh_version}`")

    compliant_contracts = []
    non_compliant_contracts = []

    for file in contract_files:
        contract_text = extract_text(file)
        contract_version = find_osh_version(contract_text)
        compliance = "✅ Compliant" if contract_version == current_osh_version and contract_version != "Not Found" else "❌ Not Compliant"
        risk = classify_risk(contract_text)
        schedules_found = check_schedules(contract_text)

        if compliance.startswith("✅"):
            compliant_contracts.append(file.name)
        else:
            non_compliant_contracts.append(file.name)

        with st.expander(f"📄 {file.name}"):
            st.markdown(f"**OSH Version Detected:** `{contract_version}`")
            st.markdown(f"**Compliance Status:** {compliance}")
            st.markdown(f"**Risk Classification:** `{risk}`")
            st.markdown(f"**Schedules Found:** {', '.join(schedules_found) if schedules_found else 'None'}`")
            st.text_area("📑 Contract Preview", contract_text[:1000], height=200)

    st.subheader("📋 Compliance Summary")
    st.success(f"✅ Compliant Contracts: {len(compliant_contracts)}")
    st.error(f"❌ Non-Compliant Contracts: {len(non_compliant_contracts)}")
    if non_compliant_contracts:
        st.markdown("**Non-Compliant List:**")
        for nc in non_compliant_contracts:
            st.markdown(f"- ❌ {nc}")

else:
    st.warning("⬆️ Please upload contract(s) and OSH reference to start.")
