import streamlit as st

from api_client import (
    APIError,
    get_conversations,
    list_businesses,
)


st.title("💬 Customer Conversations")

st.write(
    "View conversations between customers "
    "and the AskDuka assistant."
)


token = st.session_state.get("token")


if not token:
    st.error(
        "You must be logged in."
    )
    st.stop()


try:
    businesses = list_businesses(token).get("businesses", [])
except APIError as exc:
    st.error(str(exc))
    st.stop()

if not businesses:
    st.info("No businesses linked to this owner.")
    st.stop()

business_id = st.selectbox("Select business", [item["business_id"] for item in businesses])
st.caption("Conversation history will appear when WhatsApp ingestion persistence is connected.")

if st.button(
    "🔄 Refresh Conversations"
):

    try:

        result = get_conversations(
            token, business_id
        )

        conversations = result.get(
            "conversations",
            [],
        )

        if not conversations:

            st.info(
                "No conversations yet."
            )

        else:

            for conversation in conversations:

                with st.container():

                    st.write(
                        f"**Customer:** "
                        f"{conversation.get('customer_phone', 'Unknown')}"
                    )

                    st.write(
                        f"**Last message:** "
                        f"{conversation.get('last_message', '')}"
                    )

                    st.write(
                        f"**Time:** "
                        f"{conversation.get('timestamp', '')}"
                    )

                    st.divider()

    except APIError as exc:

        st.error(str(exc))
