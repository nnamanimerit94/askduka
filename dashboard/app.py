import streamlit as st

from auth import (
    is_authenticated,
    logout,
    show_login,
)


st.set_page_config(
    page_title="AskDuka",
    page_icon="💬",
    layout="wide",
)


# --------------------------------------------------
# Authentication
# --------------------------------------------------

if not is_authenticated():
    show_login()
    st.stop()


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.title("💬 AskDuka")

st.sidebar.write(
    f"Logged in as: "
    f"{st.session_state.get('email', '')}"
)

if st.sidebar.button("Logout"):
    logout()
    st.rerun()


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

st.title("💬 AskDuka")

st.subheader(
    "AI-Powered WhatsApp Business Assistant"
)

st.write(
    "Welcome to your AskDuka business dashboard."
)

st.divider()


# Dashboard metrics

col1, col2, col3 = st.columns(3)


with col1:
    st.metric(
        "Documents",
        "0",
    )


with col2:
    st.metric(
        "Conversations",
        "0",
    )


with col3:
    st.metric(
        "Status",
        "Online",
    )


st.divider()


st.subheader("Getting Started")

st.write(
    """
Use the sidebar to:

- Upload your business documents
- View customer conversations
- Configure your business settings
"""
)
