"""Image preview, upload, and analysis view."""

import streamlit as st

from frontend.api_client import APIClient, APIError
from frontend.config import MAX_UPLOAD_SIZE_MB


def render(client: APIClient) -> None:
    st.title("Image Upload and Analysis")
    st.write("Upload JPG or PNG images (maximum 50 MB).")
    uploaded_file = st.file_uploader(
        "Choose an image", type=["jpg", "jpeg", "png"], key="healthcare_image"
    )
    if uploaded_file is not None:
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        if uploaded_file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            st.error(f"File exceeds the {MAX_UPLOAD_SIZE_MB} MB upload limit.")
            return
        if st.button("Upload image"):
            try:
                result = client.upload_image(
                    uploaded_file.name, uploaded_file.getvalue()
                )
            except APIError as exc:
                st.error(str(exc))
            else:
                st.session_state.uploaded_image_id = result["image_id"]
                st.success(f"Image uploaded (ID: {result['image_id']}).")

    image_id = st.session_state.get("uploaded_image_id")
    if image_id:
        st.caption(f"Selected image ID: {image_id}")
        question = st.text_input(
            "What should the assistant inspect?",
            value="Extract and explain the readable information in this image.",
        )
        if st.button("Analyze image", type="primary"):
            with st.spinner("Analyzing image..."):
                try:
                    result = client.analyze_image(image_id, question)
                except APIError as exc:
                    st.error(str(exc))
                else:
                    st.markdown(result["analysis"])
                    st.warning(result["disclaimer"])
