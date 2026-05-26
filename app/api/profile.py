import asyncio 
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.core.pipeline import run_profiler_only

from app.services.profile_service import run_profiler, get_user_profile
router = APIRouter(prefix="/profile",tags=["Profile"])

 
@router.post("/run")
async def trigger_profiler():
    result = await asyncio.to_thread(run_profiler_only)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {
        "status":         "success",
        "message":        result["message"],
        "profiled_count": result.get("profiled_count", 0),
        "skipped_count":  result.get("skipped_count", 0),
    }
    
@router.get("/{user_id}")
def get_profile(user_id: int):
    db:Session = SessionLocal()
    
    try:
        profile = get_user_profile(user_id,db)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"No profile for user {user_id}. Run /profile/run first.")
        
        return {
            "user_id": user_id,
            "place_scores": profile["place_scores"],
            "activity_scores": profile["activity_scores"],
            "purpose_scores": profile["purpose_scores"],
            "season_scores": profile["season_scores"],
            "budget_pref": profile["budget_pref"],
        }
        
    finally: db.close()
