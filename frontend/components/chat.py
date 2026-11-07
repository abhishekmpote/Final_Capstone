"""Grounded conversational chat interface."""

import streamlit as st

from frontend.api_client import APIClient, APIError


def render(client: APIClient) -> None:
    st.title("AI Chat Assistant")
    st.caption("Answers are grounded in indexed documents; verify healthcare information with a professional.")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.pop("conversation_id", None)
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            for source in message.get("sources", []):
                page = (
                    f", page {source['page_number']}"
                    if source.get("page_number")
                    else ""
                )
                with st.expander(f"Source: {source['filename']}{page}"):
                    st.caption(
                        f"Relevance: {source['relevance_score']} · "
                        f"Document ID: {source['document_id']}"
                    )
                    st.write(source["passage"])

    question = st.chat_input("Ask about indexed documents...")
    if not question:
        return
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching sources and generating a grounded answer..."):
            try:
                result = client.chat(
                    question,
                    st.session_state.get("conversation_id"),
                    history,
                )
            except APIError as exc:
                st.error(str(exc))
                st.session_state.messages.pop()
                return
            answer = result["answer"]
            sources = result["sources"]
            st.markdown(answer)
            for source in sources:
                page = (
                    f", page {source['page_number']}"
                    if source.get("page_number")
                    else ""
                )
                with st.expander(f"Source: {source['filename']}{page}"):
                    st.caption(
                        f"Relevance: {source['relevance_score']} · "
                        f"Document ID: {source['document_id']}"
                    )
                    st.write(source["passage"])
    st.session_state.conversation_id = result["conversation_id"]
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
