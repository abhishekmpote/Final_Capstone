"""Healthcare document upload view."""

import streamlit as st

from frontend.api_client import APIClient, APIError
from frontend.config import MAX_UPLOAD_SIZE_MB


def render(client: APIClient) -> None:
    st.title("Document Upload")
    st.write("Upload PDF, DOCX, or TXT files (maximum 50 MB per file).")
    uploaded_file = st.file_uploader(
        "Choose a healthcare document", type=["pdf", "docx", "txt"]
    )
    category = st.text_input("Category (optional)", placeholder="Policy, SOP, report...")
    department = st.text_input("Department (optional)")
    patient_id = st.text_input("Patient ID filter (optional)")
    if st.button("Upload and index", type="primary", disabled=uploaded_file is None):
        if uploaded_file is None:
            return
        if uploaded_file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            st.error(f"File exceeds the {MAX_UPLOAD_SIZE_MB} MB upload limit.")
            return
        with st.spinner("Uploading document and starting ingestion..."):
            try:
                result = client.upload_document(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    category,
                    department,
                    patient_id,
                )
            except APIError as exc:
                st.error(str(exc))
            else:
                st.success(
                    f"Uploaded {result['filename']} (ID: {result['document_id']})."
                )
                st.info(
                    "Ingestion runs in the backend. Check Document Management for the latest status."
                )
