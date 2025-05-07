"""
Whisper transcription + LangChain summarisation logic.
"""

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import os
import subprocess
import tempfile
from pathlib import Path
import requests
from sqlalchemy.orm import Session
import whisper
import json

from .db import SessionLocal
from .models import Recording

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny.en")
model = whisper.load_model(WHISPER_MODEL)

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./audio_cache"))
AUDIO_DIR.mkdir(exist_ok=True)


def download_file(url: str, dest: Path):
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(1024 * 1024):
            f.write(chunk)


def extract_audio(video_path: Path, audio_path: Path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(audio_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def transcribe(audio_path: Path) -> dict:
    return model.transcribe(str(audio_path))


def run_transcription_job():
    db: Session = SessionLocal()
    recs = db.query(Recording).filter_by(transcript_fetched=False).all()
    for rec in recs:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                video_file = tmpdir / "meeting.mp4"
                download_file(rec.recording_url, video_file)

                audio_file = tmpdir / "audio.wav"
                extract_audio(video_file, audio_file)

                result = transcribe(audio_file)
                out_path = AUDIO_DIR / f"{rec.meeting_id}.json"
                out_path.write_text(json.dumps(result, indent=2))

                rec.transcript_fetched = True
                rec.transcript_path = str(out_path)
                db.commit()
        except Exception as e:
            print(f"Failed to transcribe {rec.meeting_id}: {e}")
            db.rollback()
    db.close()