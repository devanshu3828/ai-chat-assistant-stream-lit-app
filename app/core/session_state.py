"""Initialize and manage Streamlit session state."""

import uuid
import streamlit as st
from app.config.settings import DEFAULT_REGION


def initialize_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_id" not in st.session_state:
        # Session ID must be 33+ characters
        st.session_state.session_id = str(uuid.uuid4()) + str(uuid.uuid4())[:5]

    if "agent_arn" not in st.session_state:
        st.session_state.agent_arn = ""

    if "region" not in st.session_state:
        st.session_state.region = DEFAULT_REGION

    if "available_agents" not in st.session_state:
        st.session_state.available_agents = []

    if "aws_access_key_id" not in st.session_state:
        st.session_state.aws_access_key_id = ""

    if "aws_secret_access_key" not in st.session_state:
        st.session_state.aws_secret_access_key = ""

    if "aws_session_token" not in st.session_state:
        st.session_state.aws_session_token = ""

    if "credentials_configured" not in st.session_state:
        st.session_state.credentials_configured = False

