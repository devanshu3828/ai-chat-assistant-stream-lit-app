"""UI components for the Streamlit application."""

import uuid
import streamlit as st
import boto3
from app.config.settings import DEFAULT_REGION
from app.core.aws_client import fetch_available_agents


def render_credentials_setup():
    """Render the credentials setup form."""
    st.title("🔐 AWS Credentials Setup")
    st.info("Please configure your AWS credentials to continue.")
    
    with st.form("credentials_form"):
        st.subheader("AWS Credentials")
        
        form_access_key = st.text_input(
            "AWS Access Key ID",
            value=st.session_state.get("aws_access_key_id", ""),
            type="password",
            help="Your AWS Access Key ID"
        )
        
        form_secret_key = st.text_input(
            "AWS Secret Access Key",
            value=st.session_state.get("aws_secret_access_key", ""),
            type="password",
            help="Your AWS Secret Access Key"
        )
        
        form_session_token = st.text_input(
            "AWS Session Token (Optional)",
            value=st.session_state.get("aws_session_token", ""),
            type="password",
            help="Required only for temporary credentials"
        )
        
        st.divider()
        
        st.subheader("AWS Region")
        
        form_region = st.text_input(
            "AWS Region",
            value=st.session_state.get("region", DEFAULT_REGION),
            help="Enter the AWS region (e.g., us-east-1)"
        )
        
        submit = st.form_submit_button("Save & Continue", use_container_width=True)
        if submit:
            if form_access_key.strip() and form_secret_key.strip():
                st.session_state.aws_access_key_id = form_access_key.strip()
                st.session_state.aws_secret_access_key = form_secret_key.strip()
                st.session_state.aws_session_token = form_session_token.strip()
                st.session_state.region = form_region.strip() or DEFAULT_REGION
                
                # Test credentials
                try:
                    session = boto3.Session(
                        aws_access_key_id=form_access_key.strip(),
                        aws_secret_access_key=form_secret_key.strip(),
                        aws_session_token=form_session_token.strip() if form_session_token.strip() else None,
                        region_name=form_region.strip() or DEFAULT_REGION
                    )
                    test_client = session.client('sts', region_name=form_region.strip() or DEFAULT_REGION)
                    identity = test_client.get_caller_identity()
                    st.session_state.credentials_configured = True
                    st.success(f"✅ Credentials validated! Account: {identity.get('Account', 'N/A')}")
                    
                    # Fetch available agents
                    with st.spinner("Fetching available agents..."):
                        st.session_state.available_agents = fetch_available_agents(
                            form_region.strip() or DEFAULT_REGION,
                            session=session
                        )
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Invalid credentials: {str(e)}")
            else:
                st.error("Please provide both Access Key ID and Secret Access Key")


def render_sidebar():
    """Render the sidebar with agent selection and settings."""
    with st.sidebar:
        # Agent selection
        st.subheader("Select Agent")
        
        # Fetch available agents
        if st.button("🔄 Refresh Agents", use_container_width=True):
            st.session_state.available_agents = []
            st.rerun()
        
        if not st.session_state.available_agents:
            with st.spinner("Fetching available agents..."):
                st.session_state.available_agents = fetch_available_agents(st.session_state.region)
        
        if st.session_state.available_agents:
            # Create options for selectbox
            agent_options = [f"{agent['name']} ({agent['status']})" for agent in st.session_state.available_agents]
            agent_arns = [agent['arn'] for agent in st.session_state.available_agents]
            
            # Find current selection index
            current_index = 0
            if st.session_state.agent_arn:
                try:
                    current_index = agent_arns.index(st.session_state.agent_arn)
                except ValueError:
                    current_index = 0
            
            selected_agent = st.selectbox(
                "Available Agents",
                options=agent_options,
                index=current_index,
                help="Select an agent runtime to use"
            )
            
            if selected_agent:
                selected_index = agent_options.index(selected_agent)
                st.session_state.agent_arn = agent_arns[selected_index]
                selected_agent_data = st.session_state.available_agents[selected_index]
                
                # Display complete agent details
                st.divider()
                st.subheader("Agent Details")
                st.write(f"**Name:** {selected_agent_data['name']}")
                st.write(f"**Status:** {selected_agent_data['status']}")
                st.write(f"**ARN:**")
                st.code(selected_agent_data['arn'], language=None)
        else:
            st.warning("No agents found. Please check your credentials and region.")
            st.session_state.agent_arn = ""
        
        st.divider()
        
        # Show current credential status
        access_key = st.session_state.get("aws_access_key_id", "").strip()
        secret_key = st.session_state.get("aws_secret_access_key", "").strip()
        
        if access_key and secret_key:
            st.info("🔐 Credentials configured")
        else:
            st.warning("⚠️ Credentials not configured")
        
        # Option to reconfigure credentials
        if st.button("🔐 Reconfigure Credentials", use_container_width=True):
            st.session_state.credentials_configured = False
            st.session_state.aws_access_key_id = ""
            st.session_state.aws_secret_access_key = ""
            st.session_state.aws_session_token = ""
            st.rerun()
        
        st.divider()
        
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4()) + str(uuid.uuid4())[:5]
            st.rerun()

