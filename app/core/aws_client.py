"""AWS client utilities and agent management."""

import streamlit as st
import boto3


def get_boto3_client(service_name, region_name):
    """Get boto3 client with custom credentials from session state."""
    access_key = st.session_state.get("aws_access_key_id", "").strip()
    secret_key = st.session_state.get("aws_secret_access_key", "").strip()
    session_token = st.session_state.get("aws_session_token", "").strip()
    
    if not access_key or not secret_key:
        raise ValueError("AWS credentials are required. Please configure them in the setup page.")
    
    # Use custom credentials
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token if session_token else None,
        region_name=region_name
    )
    return session.client(service_name, region_name=region_name)


def fetch_available_agents(region_name, session=None):
    """Fetch all available agent runtimes from AWS."""
    try:
        if session:
            # Use provided session (for setup form)
            client = session.client('bedrock-agentcore-control', region_name=region_name)
        else:
            # Use session state credentials
            client = get_boto3_client('bedrock-agentcore-control', region_name)
        
        response = client.list_agent_runtimes()
        
        agents = []
        for runtime in response.get('agentRuntimes', []):
            agents.append({
                'arn': runtime.get('agentRuntimeArn', ''),
                'name': runtime.get('agentRuntimeName', 'Unknown'),
                'status': runtime.get('status', 'Unknown')
            })
        
        return agents
    except Exception as e:
        st.error(f"Error fetching agents: {str(e)}")
        return []

