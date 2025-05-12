#!/usr/bin/env python3
import os
import sys
# Add project root to PYTHONPATH for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from dotenv import load_dotenv

# Explicitly load .env from project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

from app.publishers import publish_to_confluence

# Use the demo transcript JSON from the demo run
meeting_id = 'confluence_test'
summary_text = 'This is a test summary from MeetMate!'
transcript_path = os.path.join(os.path.dirname(__file__), '..', 'audio_cache', 'demo_meeting_summary_123.json')

print(f"Publishing to Confluence: meeting_id={meeting_id}")
publish_to_confluence(meeting_id, summary_text, transcript_path)
print('✅ Confluence test page created!') 