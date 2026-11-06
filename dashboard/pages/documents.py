import streamlit as st

from api_client import (
    APIError,
    upload_document,
)


st.title("📄 Business Documents")

st.write(
    "Upload documents containing your "
    "business information."
)


uploaded_file = st.file_uploader(
    "Choose a document",
    type=[
        "pdf",
        "txt",
        "docx",
    ],
)


if uploaded_file:

    st.write(
        f"Selected: **{uploaded_file.name}**"
    )

    if st.button(
        "Upload Document",
        type="primary",
    ):

        token = st.session_state.get("token")

        if not token:
            st.error(
                "You must be logged in."
            )
            st.stop()

        try:

            result = upload_document(
                uploaded_file,
                token,
            )

            st.success(
                "Document uploaded successfully."
            )

            st.write(
                f"Document ID: "
                f"{result.get('document_id', 'N/A')}"
            )

            st.write(
                f"Status: "
                f"{result.get('status', 'N/A')}"
            )

        except APIError as exc:
            st.error(str(exc))
