import streamlit as st
import fitz  # PyMuPDF
import docx
import re
import pandas as pd
from io import BytesIO

# Safaricom Green Theme
safaricom_green = "#00A550"
st.set_page_config(page_title="CompliScan: Contract Analyzer", layout="wide")

# Style override for green background and white text
st.markdown(f"""
    <style>
        .main {{
            background-color: {safaricom_green};
            color: white;
        }}
        .stApp {{
            background-color: {safaricom_green};
        }}
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {{
            color: white !important;
        }}
        .stButton>button {{
            background-color: white;
            color: black;
        }}
    </style>
""", unsafe_allow_html=True)

# Show Safaricom logo
st.image("safaricom-logo.jpeg.jpeg", width=150)
st.title("CompliScan: Contract Analyzer")
st.markdown("Upload contract(s), OSH version reference, and OSH risk evaluator to detect compliance, risk, and key schedules.")

# Uploads
col1, col2, col3 = st.columns(3)
with col1:
    contract_files = st.file_uploader("📄 Upload Contract(s)", type=["pdf", "docx"], accept_multiple_files=True)
with col2:
    osh_version_file = st.file_uploader("📘 Upload OSH Version Reference", type=["pdf", "docx"])
with col3:
    osh_risk_file = st.file_uploader("📕 Upload OSH Risk Evaluator", type=["pdf", "docx"])

# Key clauses to extract
key_schedules = [
    "PRICING", "SCOPE OF WORK", "SLA", "SAFETY OSH", "SUPPLIER CODE OF CONDUCT",
    "DOCUMENT VERSION OSH", "DOCUMENT VERSION CODE OF CONDUCT",
    "LIQUIDATED DAMAGES", "PAYMENT TERMS", "INCOTERMS"
]

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
        r"Occupational\s+Safety\s+and\s+Health.*Version\s*:?[\s\-]*([0-9.]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Not Found"

def check_schedules(text):
    return [s for s in key_schedules if s.lower() in text.lower()]

def extract_risk_keywords(text):
    risk = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for level in risk:
        matches = re.findall(rf"{level}.*?:\s*(.*?)\n", text, re.IGNORECASE)
        for match in matches:
            phrases = re.split(r",|;|\n", match)
            risk[level].extend([p.strip().lower() for p in phrases if p.strip()])
    return risk

def classify_risk(text, risk_keywords):
    text_lower = text.lower()
    for level in ["HIGH", "MEDIUM", "LOW"]:
        for phrase in risk_keywords.get(level, []):
            if phrase in text_lower:
                return level
    return "Unknown"

# Run only if all 3 files are uploaded
if contract_files and osh_version_file and osh_risk_file:
    st.success("✅ Files uploaded. Analyzing...")

    version_text = extract_text(osh_version_file)
    current_osh_version = find_osh_version(version_text)
    st.info(f"📘 OSH Version Detected: `{current_osh_version}`")

    risk_text = extract_text(osh_risk_file)
    risk_keywords = extract_risk_keywords(risk_text)
    st.info("📕 Extracted Risk Keywords:")
    for level in risk_keywords:
        st.markdown(f"**{level}**: {', '.join(risk_keywords[level]) or 'None found'}")

    results = []

    for file in contract_files:
        contract_text = extract_text(file)
        contract_version = find_osh_version(contract_text)
        compliance = "✅ Compliant" if contract_version == current_osh_version else "❌ Not Compliant"
        risk = classify_risk(contract_text, risk_keywords)
        schedules = check_schedules(contract_text)

        results.append({
            "Contract Name": file.name,
            "OSH Version": contract_version,
            "Compliance": compliance,
            "Risk Level": risk,
            "Schedules Found": ", ".join(schedules)
        })

        with st.expander(f"📄 {file.name}"):
            st.markdown(f"**OSH Version Detected:** `{contract_version}`")
            st.markdown(f"**Compliance Status:** {compliance}")
            st.markdown(f"**Risk Classification:** `{risk}`")
            st.markdown(f"**Schedules Found:** {', '.join(schedules) if schedules else 'None'}")
            st.text_area("📑 Contract Preview", contract_text[:1500], height=200)

    st.subheader("📋 Compliance Summary")
    df = pd.DataFrame(results)
    st.dataframe(df)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Contract Analysis")
        writer.close()

    st.download_button(
        "📥 Download Excel Report",
        data=buffer.getvalue(),
        file_name="CompliScan_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("⬆️ Please upload contracts, OSH version reference, and OSH risk evaluator to start analysis.")
