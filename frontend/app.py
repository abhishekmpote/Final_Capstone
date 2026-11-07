"""Streamlit entry point for the healthcare assistant."""

import streamlit as st

from frontend.api_client import APIClient, APIError
from frontend.components import (
    chat,
    dashboard,
    document_management,
    document_upload,
    image_upload,
    sidebar,
)

st.set_page_config(
    page_title="Healthcare AI Assistant",
    page_icon="🏥",
    layout="wide",
)


def render_login() -> None:
    st.title("Healthcare Conversational AI Assistant")
    st.write("Sign in to search healthcare knowledge sources and manage documents.")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary")
    if submitted:
        try:
            result = APIClient().login(username, password)
        except APIError as exc:
            st.error(str(exc))
        else:
            st.session_state.access_token = result["access_token"]
            st.session_state.username = result["username"]
            st.rerun()


if not st.session_state.get("access_token"):
    render_login()
else:
    client = APIClient(st.session_state.access_token)
    selected_page = sidebar.render_sidebar()
    if selected_page == "Dashboard":
        dashboard.render(client)
    elif selected_page == "AI Chat Assistant":
        chat.render(client)
    elif selected_page == "Document Upload":
        document_upload.render(client)
    elif selected_page == "Image Upload":
        image_upload.render(client)
    elif selected_page == "Document Management":
        document_management.render(client)
