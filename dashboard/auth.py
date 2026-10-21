import streamlit as st

from api_client import APIError, login


def is_authenticated() -> bool:
    """Check whether the owner is logged in."""

    return bool(
        st.session_state.get("token")
    )


def logout() -> None:
    """Log the owner out."""

    st.session_state.pop("token", None)
    st.session_state.pop("email", None)


def show_login() -> None:
    """Display the login form."""

    st.title("🔐 AskDuka Login")

    st.write(
        "Sign in to manage your business."
    )

    email = st.text_input(
        "Email",
        placeholder="owner@example.com",
    )

    password = st.text_input(
        "Password",
        type="password",
    )

    if st.button(
        "Login",
        type="primary",
    ):
        if not email or not password:
            st.error(
                "Please enter your email and password."
            )
            return

        try:
            result = login(
                email,
                password,
            )

            token = result.get("token")

            if not token:
                st.error(
                    "The server did not return a login token."
                )
                return

            st.session_state["token"] = token
            st.session_state["email"] = email

            st.rerun()

        except APIError as exc:
            st.error(str(exc))
