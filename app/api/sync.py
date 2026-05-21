import asyncio
from fastapi import APIRouter, HTTPException
from app.services.sync_service import (
    run_full_sync,
    sync_packages,
    sync_activities,
    sync_users,
    sync_bookings
)

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/all")
async def trigger_full_sync():
    result = await asyncio.to_thread(run_full_sync)
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed for: {result['failed']}. Details: {result['results']}"
        )
    return {"status": "success", "details": result["results"]}


@router.post("/packages")
async def trigger_package_sync():
    result = await asyncio.to_thread(sync_packages)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}


@router.post("/activities")
async def trigger_activity_sync():
    result = await asyncio.to_thread(sync_activities)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}


@router.post("/users")
async def trigger_user_sync():
    result = await asyncio.to_thread(sync_users)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}


@router.post("/bookings")
async def trigger_booking_sync():
    result = await asyncio.to_thread(sync_bookings)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}