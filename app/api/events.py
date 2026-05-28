import asyncio
from fastapi import APIRouter, HTTPException
from app.core.pipeline import run_events_only, run_events_pipeline

router = APIRouter(prefix="/events",tags=["Events"])

@router.post("/sync")
async def trigger_events_sync():
    result = await asyncio.to_thread(run_events_only)
    if not result.get("success"):
        raise HTTPException(status_code = 500, detail= result.get("message"))
    return {
        "status": " success",
        "details": result,
    }
    
@router.post("/run-pipeline")
async def trigger_events_pipeline():
    result = await asyncio.to_thread(run_events_pipeline, "MANUAL")
    if not result.get("success"):
        raise HTTPException(status_code = 500, detail = str(result))
    return{
        "status": "success",
        "details": result,
    }