from fastapi import FastAPI
import os
import hmac
import hashlib
from fastapi import Request, HTTPException, Header
from .db import engine, SessionLocal, Base
from .models import Recording
from .tasks import register_tasks

app = FastAPI()
Base.metadata.create_all(bind=engine)
register_tasks(app)

@app.get("/")
async def root():
    return {"message": "MeetMate API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/webhook/zoom")
async def zoom_webhook(request: Request, authorization: str = Header(None)):
    payload = await request.body()
    secret = os.getenv("ZOOM_VERIFICATION_TOKEN").encode()
    signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, authorization):
        raise HTTPException(status_code=401, detail="Invalid signature")
    data = await request.json()
    url = data["payload"]["object"]["download_url"]
    meeting_id = data["payload"]["object"]["uuid"]

    db = SessionLocal()
    rec = Recording(platform="zoom", meeting_id=meeting_id, recording_url=url)
    db.add(rec)
    db.commit()
    db.close()
    return {"status": "ok"}
