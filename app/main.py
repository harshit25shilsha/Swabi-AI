# app/main.py
import asyncio
from fastapi import FastAPI
from app.database import create_all_tables
from app.api.sync import router as sync_router
from app.api.tagger import router as tagger_router
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.services.sync_service import run_full_sync
from app.services.tagger_service import run_tagger

app = FastAPI(
    title="Swabi AI Recommendation Service",
    version="1.0.0",
    description="AI-powered recommendation engine for Swabi travel platform"
)

app.include_router(sync_router)
app.include_router(tagger_router)


def sync_and_tag():
    run_full_sync()
    run_tagger()


@app.on_event("startup")
async def startup_event():
    print("Starting Swabi AI Service...")
    create_all_tables()
    print("Database ready.")
    start_scheduler()
    asyncio.create_task(asyncio.to_thread(sync_and_tag))
    print("Initial sync + tagging started in background.")


@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()


@app.get("/")
def root():
    return {"status": "Swabi AI is Running"}