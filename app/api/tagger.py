import json
import asyncio
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.package import PackageTags
from app.services.tagger_service import run_tagger
from app.core.pipeline import run_tagger_only

router = APIRouter(prefix="/tagger",tags=["TAGGER"])

# Mannually trigger NLP Tagging 

@router.post("/run")
async def trigger_tagger():
    result = await asyncio.to_thread(run_tagger_only)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {
        "status":        "success",
        "message":       result["message"],
        "tagged_count":  result.get("tagged_count", 0),
        "failed_count":  result.get("failed_count", 0),
    }
@router.get("/tags/{package_id}")
def get_package_tags(package_id: int):
    db: Session = SessionLocal()
    
    try:
        tags = db.query(PackageTags).filter(
            PackageTags.package_id == package_id
        ).first()
        
        if not tags:
            raise HTTPException(
                status_code=404,
                detail = f"No tags found for package {package_id}. Run /tagger/run first."
            )
            
        return {
            "package_id": tags.package_id,
            "place_types": json.loads(tags.place_types or "[]"),
            "activity_tags": json.loads(tags.activity_tags or "[]"),
            "trip_purpose": json.loads(tags.trip_purpose or "[]"),
            "season_tags": json.loads(tags.season_tags or "[]"),
            "duration_type": tags.duration_type,
            "budget_category":tags.budget_category,
            "tagged_at":tags.tagged_at,
        }
        
    finally:
        db.close()
        



@router.get("/tags")
def get_all_tags():
    db: Session = SessionLocal()
    try:
        all_tags = db.query(PackageTags).all()
        return {
            "total": len(all_tags),
            "packages": [
                {
                    "package_id":      t.package_id,
                    "place_types":     json.loads(t.place_types     or "[]"),
                    "activity_tags":   json.loads(t.activity_tags   or "[]"),
                    "trip_purpose":    json.loads(t.trip_purpose    or "[]"),
                    "season_tags":     json.loads(t.season_tags     or "[]"),
                    "duration_type":   t.duration_type,
                    "budget_category": t.budget_category,
                }
                for t in all_tags
            ]
        }
    finally:
        db.close()
 
