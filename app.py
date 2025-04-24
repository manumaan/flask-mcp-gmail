import asyncio
import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from agents import Agent, Runner, trace, gen_trace_id
from agents.mcp import MCPServerStdio
from flask import Flask, render_template, request
from server import GmailClient  # Import GmailClient from server.py

app = Flask(__name__)

# Update the path to credentials.json to be relative to app.py's location
credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

async def run_mcp_server(city):
    # Load client ID and client secret from credentials.json
    with open(credentials_path, 'r') as file:
        credentials_data = json.load(file)

    # Access client ID and client secret from the 'installed' key
    installed_data = credentials_data.get('installed', {})

    # Validate the presence of required keys in the 'installed' section
    required_keys = ['client_id', 'client_secret']
    missing_keys = [key for key in required_keys if key not in installed_data]
    if missing_keys:
        raise KeyError(f"Missing required keys in credentials.json: {', '.join(missing_keys)}")

    # Extract client ID and client secret
    client_id = installed_data['client_id']
    client_secret = installed_data['client_secret']

    # Set up the OAuth2 flow to get access and refresh tokens
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=["https://www.googleapis.com/auth/gmail.readonly"]
    )

    # Run the flow to get credentials
    credentials = flow.run_local_server(port=0)

    # Initialize the GmailClient with the obtained credentials
    gmail_client = GmailClient(
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret
    )

    # Example usage of GmailClient (replace with your actual logic)
    try:
        # Fetch recent emails using GmailClient
        response = gmail_client.get_recent_emails(max_results=5, unread_only=False)

        # Log the response for debugging
        print("Response from GmailClient:", response)

        # Log the type of the response for debugging
        print("Response type:", type(response))

        # Ensure the response is a dictionary
        if isinstance(response, str):
            response = json.loads(response)

        # Map 'from' to 'sender' for template compatibility
        emails = [
            {"sender": email.get("from"), "subject": email.get("subject")}
            for email in response.get("emails", [])
        ]

        return {
            "emails": emails,
            "summary": "Fetched 5 recent emails."
        }
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_emails', methods=['POST'])
def get_emails():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(run_mcp_server(""))
    return render_template('emails.html', response=response)

if __name__ == '__main__':
    app.run(debug=True)