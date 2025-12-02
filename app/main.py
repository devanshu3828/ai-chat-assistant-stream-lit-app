"""Main Streamlit application for AI Chat Assistant."""

import json
import sys
from pathlib import Path
import streamlit as st

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config.settings import APP_TITLE, DEFAULT_REGION
from app.core.session_state import initialize_session_state
from app.core.aws_client import get_boto3_client
from app.ui.components import render_credentials_setup, render_sidebar
from app.services.streaming import stream_agent_response, extract_assistant_message


def render_message_with_s3(text, region, unique_id=""):
    """Render message with S3 links replaced by clickable download buttons."""
    from app.services.s3_handler import render_message_with_s3_links
    
    render_message_with_s3_links(text, region, unique_id)


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Check if credentials are configured
    access_key = st.session_state.get("aws_access_key_id", "").strip()
    secret_key = st.session_state.get("aws_secret_access_key", "").strip()
    
    # If credentials are not configured, show setup page
    if not st.session_state.get("credentials_configured", False) and not (access_key and secret_key):
        render_credentials_setup()
        st.stop()

    # Main app continues here
    st.title(APP_TITLE)
    
    # Render sidebar
    render_sidebar()
    
    # Display chat history
    region = st.session_state.get("region", DEFAULT_REGION)
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_message_with_s3(message["content"], region, unique_id=f"msg_{idx}")
            else:
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("💭 Thinking...")
            
            try:
                # Get ARN and region from session state
                agent_arn = st.session_state.get("agent_arn", "")
                region = st.session_state.get("region", DEFAULT_REGION)
                
                # Validate ARN
                if not agent_arn or not agent_arn.strip():
                    raise ValueError("Please select an agent from the sidebar")
                
                # Stream the response
                assistant_message = ""
                try:
                    # Use streaming response
                    response_generator = stream_agent_response(
                        agent_arn,
                        st.session_state.session_id,
                        prompt,
                        region
                    )
                    
                    # Collect the streamed message
                    for chunk in response_generator:
                        assistant_message += chunk
                        # Show streaming text
                        message_placeholder.markdown(assistant_message + "▌")
                    
                    # Clear streaming cursor and render final message with S3 links
                    message_placeholder.empty()
                    if assistant_message:
                        render_message_with_s3(assistant_message, region, unique_id="streaming")
                    
                except Exception as stream_error:
                    # Fallback to non-streaming if streaming fails
                    st.warning(f"Streaming failed, using non-streaming mode: {str(stream_error)}")
                    
                    # Create Bedrock AgentCore client
                    client = get_boto3_client('bedrock-agentcore', region)
                    
                    # Prepare payload
                    payload = json.dumps({"message": prompt})
                    
                    # Invoke agent runtime
                    response = client.invoke_agent_runtime(
                        agentRuntimeArn=agent_arn,
                        runtimeSessionId=st.session_state.session_id,
                        payload=payload,
                        qualifier="DEFAULT"
                    )
                    
                    # Read response
                    response_body = response['response'].read()
                    response_data = json.loads(response_body)
                    
                    # Extract the assistant message
                    assistant_message = extract_assistant_message(response_data)
                    
                    # Render message with S3 download handling
                    message_placeholder.empty()
                    render_message_with_s3(assistant_message, region, unique_id="fallback")
                
                # Add to chat history
                if assistant_message:
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                message_placeholder.markdown(f"❌ {error_msg}")
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                st.error(f"Full error: {repr(e)}")


if __name__ == "__main__":
    main()

