import json 
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.booking import BookingHistory
from app.models.package import PackageTags
from app.models.profile import UserInterestProfile
from app.models.user import UserCache
from app.models.event import UserEvent
from app.models.package import PackageTags

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


# UPDATE PROFILES FROM EVENTS
VIEW_WEIGHT = 2
SEARCH_WEIGHT = 1


def update_profiles_from_events() -> dict:
    log("PROFILE UPDATE FROM EVENTS STARTED")
    db            = get_db()
    updated_count = 0
    skipped_count = 0

    try:
        from app.models.event import UserEvent

        # Only get users who have UNSCORED events
        user_ids = (
            db.query(UserEvent.user_id)
            .filter(UserEvent.scored == False)
            .distinct()
            .all()
        )
        user_ids = [u[0] for u in user_ids if u[0]]

        for user_id in user_ids:
            try:
                place_scores    = {}
                activity_scores = {}
                purpose_scores  = {}
                season_scores   = {}

                # Only unscored view events
                view_events = db.query(UserEvent).filter(
                    UserEvent.user_id    == user_id,
                    UserEvent.event_type == "package_viewed",
                    UserEvent.scored     == False
                ).all()

                for event in view_events:
                    if not event.package_id:
                        continue
                    tags = db.query(PackageTags).filter(
                        PackageTags.package_id == event.package_id
                    ).first()
                    if not tags:
                        continue
                    add_scores(place_scores,    json.loads(tags.place_types   or "[]"), VIEW_WEIGHT)
                    add_scores(activity_scores, json.loads(tags.activity_tags or "[]"), VIEW_WEIGHT)
                    add_scores(purpose_scores,  json.loads(tags.trip_purpose  or "[]"), VIEW_WEIGHT)
                    add_scores(season_scores,   json.loads(tags.season_tags   or "[]"), VIEW_WEIGHT)

                # Only unscored search events
                search_events = db.query(UserEvent).filter(
                    UserEvent.user_id    == user_id,
                    UserEvent.event_type == "search_performed",
                    UserEvent.scored     == False
                ).all()

                for event in search_events:
                    if event.state:
                        place_scores[event.state] = place_scores.get(event.state, 0) + SEARCH_WEIGHT
                    if event.country:
                        place_scores[event.country] = place_scores.get(event.country, 0) + SEARCH_WEIGHT
                    if event.search_date:
                        season = _infer_season_from_date(event.search_date)
                        if season:
                            season_scores[season] = season_scores.get(season, 0) + SEARCH_WEIGHT

                if not any([place_scores, activity_scores, purpose_scores, season_scores]):
                    skipped_count += 1
                    continue

                _merge_event_scores_into_profile(
                    user_id, place_scores, activity_scores,
                    purpose_scores, season_scores, db
                )

                # Mark all processed events as scored
                all_user_events = db.query(UserEvent).filter(
                    UserEvent.user_id == user_id,
                    UserEvent.scored  == False
                ).all()
                for e in all_user_events:
                    e.scored = True

                db.commit()
                updated_count += 1
                log(f"User {user_id} profile updated from events.")

            except Exception as e:
                db.rollback()
                skipped_count += 1
                log(f"User {user_id} event profile update failed: {e}")

    except Exception as e:
        msg = f"Event profile update error: {e}"
        log(msg)
        return {"success": False, "message": msg}

    finally:
        db.close()

    msg = f"Event profile update done - {updated_count} updated, {skipped_count} skipped."
    log(msg)
    return {"success": True, "message": msg}



def _infer_season_from_date(date_str: str) -> str | None:
    if not date_str:
        return None

    from datetime import datetime

    # Try all known formats
    formats = [
        "%d-%m-%Y",    # 28-05-2026
        "%Y-%m-%d",    # 2026-05-28
        "%d/%m/%Y",    # 28/05/2026
        "%Y/%m/%d",    # 2026/05/28
        "%d-%m-%y",    # 28-05-26
    ]

    for fmt in formats:
        try:
            date  = datetime.strptime(date_str.strip(), fmt)
            month = date.month
            if month in [3, 4, 5]:
                return "spring"
            elif month in [6, 7, 8]:
                return "summer"
            elif month in [9, 10, 11]:
                return "autumn"
            else:
                return "winter"
        except ValueError:
            continue

    log(f"Could not parse searchDate: {date_str}")
    return None

def _merge_event_scores_into_profile(
    user_id: int,
    place_scores: dict,
    activity_scores: dict,
    purpose_scores: dict,
    season_scores: dict,
    db
):
    existing = db.query(UserInterestProfile).filter(
        UserInterestProfile.user_id == user_id
    ).first()

    if existing:
        # Merge on top of existing scores
        existing_place    = json.loads(existing.place_scores    or "{}")
        existing_activity = json.loads(existing.activity_scores or "{}")
        existing_purpose  = json.loads(existing.purpose_scores  or "{}")
        existing_season   = json.loads(existing.season_scores   or "{}")

        for tag, score in place_scores.items():
            existing_place[tag] = existing_place.get(tag, 0) + score
        for tag, score in activity_scores.items():
            existing_activity[tag] = existing_activity.get(tag, 0) + score
        for tag, score in purpose_scores.items():
            existing_purpose[tag] = existing_purpose.get(tag, 0) + score
        for tag, score in season_scores.items():
            existing_season[tag] = existing_season.get(tag, 0) + score

        existing.place_scores    = json.dumps(existing_place)
        existing.activity_scores = json.dumps(existing_activity)
        existing.purpose_scores  = json.dumps(existing_purpose)
        existing.season_scores   = json.dumps(existing_season)
        existing.updated_at      = datetime.now()

    else:
        # No booking profile yet — create from events only
        db.add(UserInterestProfile(
            user_id         = user_id,
            place_scores    = json.dumps(place_scores),
            activity_scores = json.dumps(activity_scores),
            purpose_scores  = json.dumps(purpose_scores),
            season_scores   = json.dumps(season_scores),
            budget_pref     = None,
            updated_at      = datetime.now()
        ))

    db.commit()