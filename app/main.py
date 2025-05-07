from fastapi import FastAPI
import os
import hmac
import hashlib
from fastapi import Request, HTTPException, Header
from .db import engine, SessionLocal, Base
from .models import Recording
# from .tasks import register_tasks

app = FastAPI()
Base.metadata.create_all(bind=engine)
# register_tasks(app)

@app.get("/")
async def root():
    return {"message": "MeetMate API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/webhook/zoom")
async def zoom_webhook(request: Request, authorization: str = Header(None)):
    payload = await request.body()
    # Verify HMAC signature using signing secret
    secret = os.getenv("ZOOM_SIGNING_SECRET").encode()
    raw_sig = authorization or ""
    # Strip 'sha256=' prefix if present
    header_sig = raw_sig.split("=", 1)[1] if raw_sig.startswith("sha256=") else raw_sig
    computed_sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_sig, header_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")
    data = await request.json()
    # Verify verification token
    if data.get("meta", {}).get("token") != os.getenv("ZOOM_VERIFICATION_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid verification token")
    url = data["payload"]["object"]["download_url"]
    meeting_id = data["payload"]["object"]["uuid"]

    db = SessionLocal()
    rec = Recording(platform="zoom", meeting_id=meeting_id, recording_url=url)
    db.add(rec)
    db.commit()
    db.close()
    return {"status": "ok"}
