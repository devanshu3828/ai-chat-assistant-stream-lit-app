"""Main Streamlit application for AI Chat Assistant."""

import json
import streamlit as st

from app.config.settings import APP_TITLE, DEFAULT_REGION
from app.core.session_state import initialize_session_state
from app.core.aws_client import get_boto3_client
from app.ui.components import render_credentials_setup, render_sidebar
from app.services.streaming import stream_agent_response, extract_assistant_message


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
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
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
                    
                    # Create a wrapper generator that clears "Thinking..." on first chunk
                    def clear_thinking_and_stream():
                        first_chunk = True
                        for chunk in response_generator:
                            if first_chunk:
                                message_placeholder.empty()
                                first_chunk = False
                            yield chunk
                    
                    # Display streaming response using st.write_stream
                    assistant_message = st.write_stream(clear_thinking_and_stream())
                    
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
                    
                    message_placeholder.markdown(assistant_message)
                
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

