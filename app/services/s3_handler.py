"""S3 link detection and download handling."""

import re
import streamlit as st
from app.core.aws_client import get_boto3_client


def parse_s3_url(url):
    """Parse S3 URL to extract bucket and key.
    
    Returns:
        Tuple: (bucket, key) or (None, None) if invalid
    """
    s3_match = re.match(r's3://([^/]+)/(.+)', url)
    if s3_match:
        return s3_match.group(1), s3_match.group(2)
    return None, None


def render_message_with_s3_links(text, region, unique_id=""):
    """Render message with S3 markdown links replaced by clickable download buttons.
    
    Args:
        text: Message text with markdown links [text](s3://...)
        region: AWS region
        unique_id: Unique identifier to make keys unique
    """
    # Pattern to find markdown links: [text](s3://...)
    markdown_pattern = r'\[([^\]]+)\]\((s3://[^\)]+)\)'
    
    matches = list(re.finditer(markdown_pattern, text))
    
    if not matches:
        # No S3 links, render normally
        st.markdown(text, unsafe_allow_html=True)
        return
    
    # Replace S3 links with download buttons
    last_end = 0
    for idx, match in enumerate(matches):
        link_text = match.group(1)
        url = match.group(2)
        
        # Render text before the link
        if match.start() > last_end:
            st.markdown(text[last_end:match.start()], unsafe_allow_html=True)
        
        # Render download button styled as link
        bucket, key = parse_s3_url(url)
        if bucket and key:
            filename = key.split('/')[-1] or 'download'
            cache_key = f"s3_file_{hash(url)}"
            download_key = f"s3_dl_{unique_id}_{idx}_{hash(url)}"
            
            # Download file if not cached
            if cache_key not in st.session_state:
                try:
                    s3_client = get_boto3_client('s3', region)
                    response = s3_client.get_object(Bucket=bucket, Key=key)
                    file_bytes = response['Body'].read()
                    st.session_state[cache_key] = (file_bytes, filename)
                except Exception as e:
                    st.error(f"Error downloading {filename}: {str(e)}")
                    # Show original link text on error
                    st.markdown(f"[{link_text}]({url})", unsafe_allow_html=True)
                    last_end = match.end()
                    continue
            
            # Get cached file and show download button styled as link
            file_bytes, filename = st.session_state[cache_key]
            
            # Style download button to look like a link
            st.markdown(
                f"""
                <style>
                button[data-testid="baseButton-{download_key}"] {{
                    background: transparent !important;
                    border: none !important;
                    color: #0066cc !important;
                    text-decoration: underline !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    font-size: inherit !important;
                    font-family: inherit !important;
                    box-shadow: none !important;
                    cursor: pointer !important;
                    font-weight: normal !important;
                    text-align: left !important;
                    min-height: auto !important;
                    height: auto !important;
                    line-height: inherit !important;
                    display: inline !important;
                    width: auto !important;
                }}
                button[data-testid="baseButton-{download_key}"]:hover {{
                    color: #0052a3 !important;
                    background: transparent !important;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
            
            st.download_button(
                label=link_text,
                data=file_bytes,
                file_name=filename,
                mime="application/octet-stream",
                key=download_key,
                use_container_width=False
            )
        else:
            # Invalid S3 URL, show original link
            st.markdown(f"[{link_text}]({url})", unsafe_allow_html=True)
        
        last_end = match.end()
    
    # Render remaining text
    if last_end < len(text):
        st.markdown(text[last_end:], unsafe_allow_html=True)

