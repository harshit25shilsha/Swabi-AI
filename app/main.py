# app/main.py
import asyncio
from fastapi import FastAPI
from app.database import create_all_tables
from app.api.sync import router as sync_router
from app.scheduler.jobs import start_scheduler,stop_scheduler
from app.services.sync_service import run_full_sync

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
    start_scheduler()
    asyncio.create_task(asyncio.to_thread(run_full_sync))
    print("Initial Sync Started in background")
    


@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()


## ROUTERS
app.include_router(sync_router)

@app.get("/")
def root():
    return {"status": "Swabi AI is Running"}
