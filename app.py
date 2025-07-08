import streamlit as st
import fitz  # PyMuPDF for PDF
import docx

st.set_page_config(page_title="CompliScan: Contract Analyzer", layout="wide")
st.title("🛡️ CompliScan: Contract Analyzer")
st.markdown("Upload contracts and your OSH reference document to begin analysis.")

col1, col2 = st.columns(2)

with col1:
    contract_files = st.file_uploader("📄 Upload Contract(s)", type=["pdf", "docx"], accept_multiple_files=True)

with col2:
    osh_file = st.file_uploader("📘 Upload OSH Reference Document", type=["pdf", "docx"])

def extract_text(file):
    if file.name.endswith(".pdf"):
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return "\n".join([page.get_text() for page in doc])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

if contract_files and osh_file:
    st.success("✅ Files uploaded. Extracting text...")

    osh_text = extract_text(osh_file)
    st.subheader("📘 OSH Reference Preview")
    st.text_area("OSH Document (first 1000 characters)", osh_text[:1000], height=200)

    for file in contract_files:
        contract_text = extract_text(file)
        st.subheader(f"📄 {file.name}")
        st.text_area("Contract Preview", contract_text[:1000], height=200)

    st.info("✅ STEP 1 COMPLETE: File extraction working.")
else:
    st.warning("⬆️ Please upload at least one contract and the OSH reference.")
