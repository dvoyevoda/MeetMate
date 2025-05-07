import os
import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal, engine
from app.models import Base, Recording

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    # Reset DB schema before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def sign_payload(data: bytes) -> str:
    # Use dummy signing secret if not provided in environment
    secret = os.getenv("ZOOM_SIGNING_SECRET", "testsigningsecret")
    sig = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def test_zoom_webhook_records_entry():
    # Construct fake Zoom event
    payload = {
        # Use dummy verification token if not provided in environment
        "meta": {"token": os.getenv("ZOOM_VERIFICATION_TOKEN", "testverificationtoken")},
        "payload": {
            "object": {
                "download_url": "https://example.com/fake.mp4",
                "uuid": "test-uuid-123"
            }
        }
    }
    body = json.dumps(payload).encode()
    headers = {
        "Authorization": sign_payload(body),
        "Content-Type": "application/json"
    }
    # Send to FastAPI endpoint
    response = client.post("/webhook/zoom", data=body, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Verify DB insert
    db = SessionLocal()
    recs = db.query(Recording).all()
    db.close()

    assert len(recs) == 1
    rec = recs[0]
    assert rec.meeting_id == "test-uuid-123"
    assert rec.recording_url == "https://example.com/fake.mp4"
