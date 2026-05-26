import asyncio
from fastapi import APIRouter, HTTPException
from app.core.pipeline import run_pipeline

router = APIRouter(prefix="/sync", tags=["Sync"])
from app.services.sync_service import sync_packages, sync_activities, sync_users, sync_bookings


@router.post("/all")
async def trigger_full_sync():
    result = await asyncio.to_thread(run_pipeline, "SYNC API")
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Full pipeline failed."),
        )
    return {
        "status": "success",
        "message": result["message"],
        "sync": result["sync"],
        "tagger": result["tagger"],
        "profiler": result["profiler"],
    }


@router.post("/packages")
async def trigger_package_sync():
    result = await asyncio.to_thread(sync_packages)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}


@router.post("/activities")
async def trigger_activity_sync():
    result = await asyncio.to_thread(sync_activities)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}



@router.post("/users")
async def trigger_user_sync():
    result = await asyncio.to_thread(sync_users)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}


@router.post("/bookings")
async def trigger_booking_sync():
    result = await asyncio.to_thread(sync_bookings)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}
