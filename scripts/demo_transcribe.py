#!/usr/bin/env python3
import sys
import os
# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Skip loading .env so we don't pick up DATABASE_URL pointing to Postgres
os.environ["SKIP_DOTENV"] = "1"
# Override the database URL to use an in-memory SQLite for demo purposes
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

try:
    import json
    from pathlib import Path
    from app.db import Base, engine, SessionLocal
    from app.models import Recording
    from app.summarizer import run_transcription_job, AUDIO_DIR
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("\nTry running this script with your virtual environment Python:")
    print("source .venv/bin/activate  # Activate your venv first")
    print("python scripts/demo_transcribe.py")
    sys.exit(1)

# Check if audio_cache directory exists
if not os.path.exists(AUDIO_DIR):
    print(f"Creating audio cache directory: {AUDIO_DIR}")
    os.makedirs(AUDIO_DIR, exist_ok=True)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Insert a demo recording (change port if needed)
server_port = 8001  # Change this if your server is on a different port
db = SessionLocal()
recording = Recording(
    platform="test",
    meeting_id="demo123",
    recording_url=f"http://localhost:{server_port}/sample.mp4"
)

# Check if recording already exists
existing = db.query(Recording).filter_by(meeting_id="demo123").first()
if existing:
    print(f"Using existing recording: {existing.meeting_id}")
    recording = existing
else:
    print(f"Creating new recording: {recording.meeting_id}")
    db.add(recording)
    db.commit()

meeting_id = recording.meeting_id  # cache before closing session
db.close()

# Run the transcription pipeline
print(f"Running transcription job for {meeting_id}...")
try:
    run_transcription_job()
except Exception as e:
    print(f"Error during transcription: {e}")
    print("\nMake sure:")
    print(f"1. HTTP server is running: python -m http.server {server_port} --directory docs/assets")
    print("2. sample.mp4 exists in docs/assets")
    print("3. ffmpeg is installed: brew install ffmpeg")
    sys.exit(1)

# Locate and print the transcript
transcript_file = AUDIO_DIR / f"{meeting_id}.json"
print(f"Transcript JSON path: {transcript_file}")

if transcript_file.exists():
    try:
        data = json.loads(transcript_file.read_text())
        print("\nTranscription successful!")
        print(f"Transcript text:\n{data.get('text', '<no text key>')}")
    except Exception as e:
        print(f"Error reading transcript file: {e}")
else:
    print("\nERROR: Transcript file not found.")
    print("Make sure:")
    print(f"1. HTTP server is running: python -m http.server {server_port} --directory docs/assets")
    print("2. sample.mp4 exists in docs/assets")
    print("3. ffmpeg is installed: brew install ffmpeg")

# Override engine and SessionLocal to use in-memory SQLite for the demo
engine = create_engine(
    "sqlite:///:memory:",
    echo=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine) 