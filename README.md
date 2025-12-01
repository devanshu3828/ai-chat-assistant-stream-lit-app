# AI Chat Assistant

A production-ready Streamlit application for interacting with AWS Bedrock AgentCore agents through a chat interface.

## Features

- 🤖 Interactive chat interface with AWS Bedrock AgentCore agents
- 🔄 Real-time streaming responses
- 🔐 Secure AWS credentials management
- 📋 Agent selection and management
- 💬 Chat history persistence

## Project Structure

```
ai-chat-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py        # Application configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── session_state.py   # Session state management
│   │   └── aws_client.py      # AWS client utilities
│   ├── services/
│   │   ├── __init__.py
│   │   └── streaming.py       # Streaming response handling
│   └── ui/
│       ├── __init__.py
│       └── components.py      # UI components
├── requirements.txt
└── README.md
```

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
streamlit run app/main.py
```

## Configuration

The application requires AWS credentials to be configured:
- AWS Access Key ID
- AWS Secret Access Key
- AWS Session Token (optional, for temporary credentials)
- AWS Region

Credentials can be configured through the UI on first launch.

## Requirements

- Python 3.8+
- Streamlit 1.28.0+
- boto3 1.28.0+

## License

MIT

