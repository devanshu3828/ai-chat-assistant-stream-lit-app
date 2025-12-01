"""Streaming response handling."""

import json
import time
from app.core.aws_client import get_boto3_client


def extract_assistant_message(response_data):
    """Extract assistant message from response data."""
    assistant_message = ""
    
    if isinstance(response_data, dict) and "result" in response_data:
        result = response_data["result"]
        
        if "response" in result:
            assistant_message = result["response"]
        elif "messages" in result and isinstance(result["messages"], list) and len(result["messages"]) > 1:
            assistant_msg = result["messages"][1]
            if isinstance(assistant_msg, list) and len(assistant_msg) > 0:
                assistant_message = assistant_msg[0]
            else:
                assistant_message = str(assistant_msg)
        else:
            assistant_message = json.dumps(result, indent=2)
    else:
        assistant_message = json.dumps(response_data, indent=2)
    
    return assistant_message


def stream_agent_response(agent_arn, session_id, prompt, region_name):
    """Stream agent response by simulating streaming from complete response."""
    try:
        # Create Bedrock AgentCore client
        client = get_boto3_client('bedrock-agentcore', region_name)
        
        # Prepare payload
        payload = json.dumps({"message": prompt})
        
        # Invoke agent runtime
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier="DEFAULT"
        )
        
        # Read the response
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        # Extract the assistant message
        assistant_message = extract_assistant_message(response_data)
        
        # Simulate streaming by yielding words/sentences
        # This provides a better UX even if the API doesn't support true streaming
        if assistant_message:
            # Split into words and yield incrementally
            words = assistant_message.split(' ')
            
            for i, word in enumerate(words):
                # Yield only the new word with a space (except for the last word)
                if i < len(words) - 1:
                    yield word + " "
                else:
                    yield word
                
                # Small delay to make streaming visible (optional)
                time.sleep(0.02)  # 20ms delay between words
                
    except Exception as e:
        raise Exception(f"Error streaming response: {str(e)}")

