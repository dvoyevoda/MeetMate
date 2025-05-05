from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "MeetMate API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
