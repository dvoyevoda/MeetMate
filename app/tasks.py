"""Background jobs / Celery tasks: Google Meet polling."""
import os
from fastapi_utils.tasks import repeat_every
from fastapi import FastAPI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from .db import SessionLocal
from .models import Recording
from .summarizer import run_transcription_job

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
creds = service_account.Credentials.from_service_account_file(
    os.getenv("GOOGLE_CREDENTIALS_PATH"), scopes=SCOPES
)
drive = build("drive", "v3", credentials=creds)

def register_tasks(app: FastAPI):
    @app.on_event("startup")
    @repeat_every(seconds=60)
    def poll_google_recordings():
        db = SessionLocal()
        results = drive.files().list(q="mimeType='video/mp4'").execute()
        for f in results.get("files", []):
            url = f.get("webContentLink")
            meeting_id = f.get("id")
            exists = db.query(Recording).filter_by(meeting_id=meeting_id).first()
            if not exists:
                rec = Recording(platform="google_meet", meeting_id=meeting_id, recording_url=url)
                db.add(rec)
                db.commit()
        db.close()

        # Run Whisper transcription for any newly downloaded recordings
        run_transcription_job()
