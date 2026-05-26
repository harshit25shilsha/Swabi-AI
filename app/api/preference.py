import json
import asyncio
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.preference import UserPreference
from app.services.preference_service import get_user_preferences
from app.services.sync_service import sync_preferences
from app.core.pipeline import run_preferences_only


router = APIRouter(prefix="/preferences", tags=["Preferences"])

@router.post("/sync")
async def trigger_preference_sync():
    result = await asyncio.to_thread(run_preferences_only)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {"status": "success", "message": result["message"]}

@router.get("/raw/{user_id}")
def get_raw_preference(user_id: int):
    db: Session = SessionLocal()
    try:
        pref = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

        if not pref:
            raise HTTPException(
                status_code=404,
                detail=f"No preferences for user {user_id}. Run /preferences/sync first."
            )

        return {
            "user_id":       user_id,
            "activity_types": json.loads(pref.activity_types or "[]"),
            "place_types":    json.loads(pref.place_types    or "[]"),
            "season":         json.loads(pref.season         or "[]"),
            "trip_purposes":  json.loads(pref.trip_purposes  or "[]"),
            "trip_duration":  json.loads(pref.trip_duration  or "[]"),
            "countries":      json.loads(pref.countries      or "[]"),
            "updated_at":     pref.updated_at,
        }
    finally:
        db.close()


@router.get("/mapped/{user_id}")
def get_mapped_preference(user_id: int):
    db: Session = SessionLocal()
    try:
        mapped = get_user_preferences(user_id, db)

        if not mapped:
            raise HTTPException(
                status_code=404,
                detail=f"No preferences for user {user_id}. Run /preferences/sync first."
            )

        return {
            "user_id":       user_id,
            "activity_tags": mapped["activity_tags"],
            "place_types":   mapped["place_types"],
            "trip_purpose":  mapped["trip_purpose"],
            "season_tags":   mapped["season_tags"],
            "duration_types": mapped["duration_types"],
        }
    finally:
        db.close()