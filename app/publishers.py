import os
import json
import requests
from pathlib import Path

# Slack configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Confluence configuration
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")         # e.g. https://your-domain.atlassian.net/wiki
CONFLUENCE_USER = os.getenv("CONFLUENCE_USER")                 # Atlassian account email
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")       # Atlassian API token
CONFLUENCE_SPACE = os.getenv("CONFLUENCE_SPACE")               # Confluence space key
CONFLUENCE_PARENT_ID = os.getenv("CONFLUENCE_PARENT_ID")       # Parent page ID for new pages


def publish_to_slack(meeting_id: str, summary: str) -> None:
    """
    Send the summary text to a Slack channel via Incoming Webhook.
    """
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL not set. Cannot post to Slack.")
    payload = {
        "text": f"*Meeting Summary ({meeting_id})*\n{summary}"
    }
    resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    resp.raise_for_status()


def publish_to_confluence(meeting_id: str, summary: str, transcript_path: str) -> None:
    """
    Create a new Confluence page with the meeting summary and full transcript.
    """
    # Validate env vars
    required = [CONFLUENCE_BASE_URL, CONFLUENCE_USER, CONFLUENCE_API_TOKEN, CONFLUENCE_SPACE, CONFLUENCE_PARENT_ID]
    if not all(required):
        raise ValueError("Confluence environment vars incomplete. Cannot post to Confluence.")

    # Read transcript text
    transcript_text = ""
    try:
        with open(transcript_path, 'r') as f:
            data = json.load(f)
            transcript_text = data.get("text", "")
    except Exception as e:
        raise RuntimeError(f"Failed to read transcript: {e}")

    # Build page content in Confluence storage format
    title = f"Meeting Summary: {meeting_id}"
    # Wrap text in simple HTML
    summary_html = summary.replace("\n", "<br/>")
    transcript_html = transcript_text.replace("\n", "<br/>")
    page_body = (
        f"<h1>{title}</h1>"
        f"<h2>Summary</h2><p>{summary_html}</p>"
        f"<h2>Transcript</h2><p>{transcript_html}</p>"
    )

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/"
    headers = {"Content-Type": "application/json"}
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE},
        "ancestors": [{"id": int(CONFLUENCE_PARENT_ID)}],
        "body": {"storage": {"value": page_body, "representation": "storage"}}
    }
    resp = requests.post(
        url,
        json=payload,
        headers=headers,
        auth=(CONFLUENCE_USER, CONFLUENCE_API_TOKEN),
        timeout=20
    )
    resp.raise_for_status() 