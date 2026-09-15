import streamlit as st


st.title("⚙️ Settings")

st.subheader("Business Settings")


business_name = st.text_input(
    "Business name",
    placeholder="My Business",
)


st.subheader("Account")

st.write(
    f"Logged in as: "
    f"{st.session_state.get('email', 'Unknown')}"
)


if st.button(
    "Save Settings",
    type="primary",
):

    if not business_name:

        st.warning(
            "Please enter a business name."
        )

    else:

        st.success(
            "Settings saved."
        )
