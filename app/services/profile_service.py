import json 
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.booking import BookingHistory
from app.models.package import PackageTags
from app.models.profile import UserInterestProfile
from app.models.user import UserCache

def log(msg:str):
    print(f"[PROFILE {datetime.now().strftime('%H:%M:%S')}] {msg}")
    
def get_db()->Session:
        return SessionLocal()
    
# SCORING WEIGHTS

BOOKING_WEIGHT = 5

# HELPER - add tag scores into score dict

def add_scores(score_dict: dict, tags: list, weight: int)-> dict:
    for tag in tags:
        if tag:
            score_dict[tag] = score_dict.get(tag,0)+ weight
    return score_dict


# BUILD PROFILE FOR ONE USER 


def build_user_profile(user_id: int, db: Session) -> dict | None:
    place_scores    = {}
    activity_scores = {}
    purpose_scores  = {}
    season_scores   = {}
    budget_counts   = {}
 
    bookings = db.query(BookingHistory).filter(
        BookingHistory.user_id == user_id
    ).all()
 
    if not bookings:
        return None

    used_booking_count = 0

    for booking in bookings:
        if booking.booking_status == "CANCELLED":
            continue
 
        tags = db.query(PackageTags).filter(
            PackageTags.package_id == booking.package_id
        ).first()
 
        if not tags:
            continue

        used_booking_count += 1
 
        place_types   = json.loads(tags.place_types    or "[]")
        activity_tags = json.loads(tags.activity_tags  or "[]")
        trip_purpose  = json.loads(tags.trip_purpose   or "[]")
        season_tags   = json.loads(tags.season_tags    or "[]")
        budget_cat    = tags.budget_category
 
        add_scores(place_scores,    place_types,   BOOKING_WEIGHT)
        add_scores(activity_scores, activity_tags, BOOKING_WEIGHT)
        add_scores(purpose_scores,  trip_purpose,  BOOKING_WEIGHT)
        add_scores(season_scores,   season_tags,   BOOKING_WEIGHT)
 
        if budget_cat:
            budget_counts[budget_cat] = budget_counts.get(budget_cat, 0) + 1
 
    budget_pref = (
        max(budget_counts, key=budget_counts.get)
        if budget_counts else None
    )

    if used_booking_count == 0:
        return None

    if not any([place_scores, activity_scores, purpose_scores, season_scores, budget_pref]):
        return None
 
    return {
        "place_scores":    place_scores,
        "activity_scores": activity_scores,
        "purpose_scores":  purpose_scores,
        "season_scores":   season_scores,
        "budget_pref":     budget_pref,
    }
 
 
# SAVE OR UPDATE PROFILE IN DB 

def save_user_profile(user_id: int , profile: dict, db: Session):
    existing = db.query(UserInterestProfile).filter(
        UserInterestProfile.user_id == user_id
    ).first()
    
    if existing:
        existing.place_scores = json.dumps(profile["place_scores"])
        existing.activity_scores = json.dumps(profile["activity_scores"])
        existing.purpose_scores = json.dumps(profile["purpose_scores"])
        existing.season_scores = json.dumps(profile["season_scores"])
        existing.budget_pref = (profile["budget_pref"])
        existing.updated_at = datetime.now()
    
    else:
        db.add(UserInterestProfile(
            user_id = user_id,
            place_scores = json.dumps(profile["place_scores"]),
            activity_scores = json.dumps(profile["activity_scores"]),
            purpose_scores = json.dumps(profile["purpose_scores"]),
            season_scores = json.dumps(profile["season_scores"]),
            budget_pref = profile["budget_pref"],
            updated_at = datetime.now()
        ))
        
    db.commit()
    
    # BUILD PROFILES FOR ALL USERS 
    
def run_profiler()->dict:
    log("PROFILER STARTED")
    db = get_db()
    profiled_count =0
    skipped_count = 0
    
    try:
        users = db.query(UserCache).all()
        
        for user in users:
            try:
                profile = build_user_profile(user.user_id,db)
                
                if not profile:
                    skipped_count+=1
                    log(f"User {user.user_id} - no usable bookings, skipped.")
                    continue
                save_user_profile(user.user_id, profile, db)
                profiled_count+=1
                
                log(f"User {user.user_id} | {user.first_name} {user.last_name}")
                log(f"  place_scores:    {profile['place_scores']}")
                log(f"  activity_scores: {profile['activity_scores']}")
                log(f"  purpose_scores:  {profile['purpose_scores']}")
                log(f"  season_scores:   {profile['season_scores']}")
                log(f"  budget_pref:     {profile['budget_pref']}")
            
            except Exception as e:
                db.rollback()
                skipped_count+=1
                log(f"User {user.user_id} failed: {e}")

    except Exception as e:
        msg = f"Profiler error: {e}"
        log(msg)
        return {"success": False, "message":msg}
    
    finally:
        db.close()
        
    msg = f"Profiler done - {profiled_count} profiled, {skipped_count} skipped."
    log(msg)
    return {
        "success": True,
        "message": msg,
        "profiled_count": profiled_count,
        "skipped_count": skipped_count,
    }
    
# GET PROFILE FOR ONE USER

def get_user_profile(user_id: int, db: Session) -> dict | None:
    profile = db.query(UserInterestProfile).filter(
        UserInterestProfile.user_id == user_id
    ).first()
 
    if not profile:
        return None
 
    return {
        "place_scores":    json.loads(profile.place_scores    or "{}"),
        "activity_scores": json.loads(profile.activity_scores or "{}"),
        "purpose_scores":  json.loads(profile.purpose_scores  or "{}"),
        "season_scores":   json.loads(profile.season_scores   or "{}"),
        "budget_pref":     profile.budget_pref,
    }
