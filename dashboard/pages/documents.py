import streamlit as st

from api_client import APIError, list_businesses, list_documents, upload_document

st.title("📄 Business Documents")
st.write("Manage text documents for a business you own.")

token = st.session_state.get("token")
if not token:
    st.error("Please sign in to manage documents.")
    st.stop()

try:
    businesses = list_businesses(token).get("businesses", [])
except APIError as exc:
    st.error(str(exc))
    st.stop()

if not businesses:
    st.info("No businesses are linked to your account yet. Ask an administrator to provision your business membership.")
    st.stop()

business_ids = [item["business_id"] for item in businesses]
business_id = st.selectbox("Select business", business_ids)

try:
    documents = list_documents(token, business_id).get("documents", [])
    if documents:
        st.dataframe(documents, use_container_width=True)
    else:
        st.info("No documents uploaded for this business yet.")
except APIError as exc:
    st.error(str(exc))

st.caption("Current upload support: UTF-8 .txt files only, maximum 256 KiB.")
uploaded_file = st.file_uploader("Choose a text document", type=["txt"])
if uploaded_file and st.button("Upload Document", type="primary"):
    try:
        result = upload_document(uploaded_file, token, business_id)
        st.success(f"Document uploaded: {result.get('document_id', 'N/A')}")
        st.rerun()
    except APIError as exc:
        st.error(str(exc))
