import streamlit as st

from api_client import (
    APIError,
    get_conversations,
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


if st.button(
    "🔄 Refresh Conversations"
):

    try:

        result = get_conversations(
            token
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
