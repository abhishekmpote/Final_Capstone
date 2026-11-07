"""Uploaded document status and authorized deletion view."""

import streamlit as st

from frontend.api_client import APIClient, APIError


def render(client: APIClient) -> None:
    st.title("Document Management")
    if st.button("Refresh documents"):
        st.rerun()
    try:
        documents = client.documents()
    except APIError as exc:
        st.error(str(exc))
        return
    if not documents:
        st.info("No documents have been uploaded.")
        return
    for document in documents:
        with st.container(border=True):
            st.subheader(document["filename"])
            st.caption(
                f"Uploaded {document['uploaded_at']} · {document['file_size']:,} bytes · "
                f"ID: {document['document_id']}"
            )
            status = document["processing_status"]
            st.write(f"**Status:** {status}")
            if document.get("error"):
                st.error(document["error"])
            left, right = st.columns(2)
            if status in {"failed", "pending"} and left.button(
                "Retry ingestion", key=f"retry-{document['document_id']}"
            ):
                try:
                    client.trigger_ingestion(document["document_id"])
                except APIError as exc:
                    st.error(str(exc))
                else:
                    st.info("Ingestion queued. Refresh to see the updated status.")
            if right.button("Delete", key=f"delete-{document['document_id']}"):
                try:
                    client.delete_document(document["document_id"])
                except APIError as exc:
                    st.error(str(exc))
                else:
                    st.success("Document deleted.")
                    st.rerun()
