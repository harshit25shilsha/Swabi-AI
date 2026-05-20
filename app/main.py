from fastapi import FastAPI
from app.database import create_all_tables

app = FastAPI(
    title="Swabi AI Recommendation Service",
    version="1.0.0",
    description="AI-powered recommendation engine for Swabi travel platform"
)


@app.on_event("startup")
async def startup_event():
    print("Starting Swabi AI Service...")
    create_all_tables()
    print("Database ready.")


@app.get("/health")
def health():
    return {"status": "Swabi AI is Running"}