from fastapi import FastAPI
from app.core.config import Settings, get_settings


app = FastAPI(
    title="My-tutor-ai",
    description="ai platform which helps tutor to track their students and lessons",
    version="0.0.1"
)

@app.get("/")
async def root():
    return {"message" : "Hello World"}

