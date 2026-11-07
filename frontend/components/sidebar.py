"""Application navigation."""

import streamlit as st

from frontend.api_client import APIClient, APIError


def render_sidebar() -> str:
    """Render the authenticated user's navigation menu."""
    st.sidebar.title("Healthcare Assistant")
    st.sidebar.caption(f"Signed in as {st.session_state.get('username', '')}")
    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "AI Chat Assistant",
            "Document Upload",
            "Image Upload",
            "Document Management",
        ],
    )
    if st.sidebar.button("Logout", use_container_width=True):
        try:
            APIClient(st.session_state.get("access_token")).logout()
        except APIError as exc:
            st.sidebar.warning(f"Could not revoke the backend session: {exc}")
        for key in ("access_token", "username", "messages", "conversation_id", "uploaded_image_id"):
            st.session_state.pop(key, None)
        st.rerun()
    return page
