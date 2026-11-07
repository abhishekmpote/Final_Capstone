"""Dashboard metrics and recent document status."""

import streamlit as st

from frontend.api_client import APIClient, APIError


def render(client: APIClient) -> None:
    st.title("Dashboard")
    st.caption("Overview of your uploaded healthcare knowledge sources.")
    if st.button("Refresh dashboard"):
        st.rerun()
    try:
        counts = client.dashboard()
    except APIError as exc:
        st.error(str(exc))
        return
    columns = st.columns(5)
    labels = (
        ("total_documents", "Uploaded documents"),
        ("indexed_documents", "Indexed documents"),
        ("pending_documents", "Pending"),
        ("failed_documents", "Failed"),
        ("total_images", "Uploaded images"),
    )
    for column, (key, label) in zip(columns, labels):
        column.metric(label, counts[key])
