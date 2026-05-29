import json
from datetime import datetime
 
from sqlalchemy.orm import Session
 
from app.database import SessionLocal
from app.models.package import PackageCache, PackageTags
from app.models.activity import ActivityCache
from app.models.profile import UserInterestProfile
from app.services.preference_service import get_user_preferences
from app.services.tagger_service import CATEGORY_TO_ACTIVITY_TAG
from app.models.booking import BookingHistory
from sqlalchemy import func

 
def log(msg: str):
    print(f"[REC {datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_db()-> Session:
    return SessionLocal()

# SCORING WEIGHTS
# Preferences = explicit started intent = higher weight
# Profile = implicit behaviour = medium weight

PREFERENCE_WEIGHT = 10
PROFILE_WEIGHT = 5
BUDGET_MATCH = 8
DURATION_MATCH = 5 
TRENDING_BOOST = 3

# SCORE ONE PACKAGE AGAINST USER 
# Combines preference tags + profile scores

def score_package(
    tags: PackageTags,
    profile: dict | None,
    preferences: dict | None,
) -> float:
    score = 0.0
 
    place_types   = json.loads(tags.place_types    or "[]")
    activity_tags = json.loads(tags.activity_tags  or "[]")
    trip_purpose  = json.loads(tags.trip_purpose   or "[]")
    season_tags   = json.loads(tags.season_tags    or "[]")
 
    # ── Preference scoring (higher weight — explicit intent) ──
    if preferences:
        for tag in place_types:
            if tag in preferences.get("place_types", []):
                score += PREFERENCE_WEIGHT
 
        for tag in activity_tags:
            if tag in preferences.get("activity_tags", []):
                score += PREFERENCE_WEIGHT
 
        for tag in trip_purpose:
            if tag in preferences.get("trip_purpose", []):
                score += PREFERENCE_WEIGHT
 
        for tag in season_tags:
            if tag in preferences.get("season_tags", []):
                score += PREFERENCE_WEIGHT
 
        # Duration match from preferences
        if tags.duration_type and tags.duration_type in preferences.get("duration_types", []):
            score += DURATION_MATCH
 
        # Budget match from preferences (infer from activity_tags luxury signal)
        if "luxury" in preferences.get("activity_tags", []) and tags.budget_category == "luxury":
            score += BUDGET_MATCH
 
    # ── Profile scoring (medium weight — implicit behaviour) ──
    if profile:
        place_scores    = profile.get("place_scores",    {})
        activity_scores = profile.get("activity_scores", {})
        purpose_scores  = profile.get("purpose_scores",  {})
        season_scores   = profile.get("season_scores",   {})
        budget_pref     = profile.get("budget_pref")
 
        for tag in place_types:
            score += place_scores.get(tag, 0) * PROFILE_WEIGHT * 0.1
 
        for tag in activity_tags:
            score += activity_scores.get(tag, 0) * PROFILE_WEIGHT * 0.1
 
        for tag in trip_purpose:
            score += purpose_scores.get(tag, 0) * PROFILE_WEIGHT * 0.1
 
        for tag in season_tags:
            score += season_scores.get(tag, 0) * PROFILE_WEIGHT * 0.1
 
        # Budget preference match
        if budget_pref and tags.budget_category == budget_pref:
            score += BUDGET_MATCH
 
    return round(score, 2)
 



# GET PERSONALIZED PACKAGE RECOMMENDATIONS

def get_recommended_packages(user_id: int, limit: int = 10) -> list[dict]:
    db = get_db()
    try:
        profile     = _get_profile(user_id, db)
        preferences = get_user_preferences(user_id, db)
 
        # Get all active tagged packages
        all_tags = db.query(PackageTags).all()
        scored   = []
 
        for tags in all_tags:
            package = db.query(PackageCache).filter(
                PackageCache.package_id == tags.package_id,
                PackageCache.package_status == "TRUE"
            ).first()
 
            if not package:
                continue
 
            score = score_package(tags, profile, preferences)
 
            scored.append({
                "package_id":      package.package_id,
                "package_name":    package.package_name,
                "country":         package.country,
                "state":           package.state,
                "no_of_days":      package.no_of_days,
                "total_price":     package.total_price,
                "place_types":     json.loads(tags.place_types    or "[]"),
                "activity_tags":   json.loads(tags.activity_tags  or "[]"),
                "season_tags":     json.loads(tags.season_tags    or "[]"),
                "duration_type":   tags.duration_type,
                "budget_category": tags.budget_category,
                "score":           score,
            })
 
        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]
 
    finally:
        db.close()
        


# GET PERSONALIZED ACTIVITY RECOMMENDATIONS

def get_recommended_activities(user_id: int, limit: int = 10)-> list[dict]:
    db = get_db()
    
    try:
        profile = _get_profile(user_id, db)
        preferences = get_user_preferences(user_id, db)
        
        activities = db.query(ActivityCache).all()
        scored = []
        
        for activity in activities:
            score = 0.0
            
            # score from preferences 
            if preferences:
                pref_activities = preferences.get("activity_tags", [])
                
                # Map activity category to our tags
                act_tags = CATEGORY_TO_ACTIVITY_TAG.get(activity.category,[])
                for tag in act_tags:
                    if tag in pref_activities:
                        score += PREFERENCE_WEIGHT
                        
            # score from profile
            if profile:
                activity_scores = profile.get("activity_scores", {})
                act_tags = CATEGORY_TO_ACTIVITY_TAG.get(activity.category, [])
                for tag in act_tags:
                    score += activity_scores.get(tag, 0) * PROFILE_WEIGHT * 0.1

            scored.append({
                "activity_id":   activity.activity_id,
                "activity_name": activity.activity_name,
                "category":      activity.category,
                "best_time":     activity.best_time,
                "country":       activity.country,
                "state":         activity.state,
                "price":         activity.price,
                "score":         round(score, 2),
            })

        scored.sort(key = lambda x: x["score"], reverse = True)
        return scored[:limit]
    
    finally:
        db.close()
        


# GET SIMILAR PACKAGES
# Based on tag overlap — Jaccard similarity

 
def get_similar_packages(package_id: int, limit: int = 6) -> list[dict]:
    db = get_db()
    try:
        source_tags = db.query(PackageTags).filter(
            PackageTags.package_id == package_id
        ).first()
 
        if not source_tags:
            return []
 
        source_place    = set(json.loads(source_tags.place_types    or "[]"))
        source_activity = set(json.loads(source_tags.activity_tags  or "[]"))
        source_purpose  = set(json.loads(source_tags.trip_purpose   or "[]"))
        source_all      = source_place | source_activity | source_purpose
 
        all_tags = db.query(PackageTags).filter(
            PackageTags.package_id != package_id
        ).all()
 
        scored = []
 
        for tags in all_tags:
            package = db.query(PackageCache).filter(
                PackageCache.package_id == tags.package_id,
                PackageCache.package_status == "TRUE"
            ).first()
 
            if not package:
                continue
 
            candidate_place    = set(json.loads(tags.place_types    or "[]"))
            candidate_activity = set(json.loads(tags.activity_tags  or "[]"))
            candidate_purpose  = set(json.loads(tags.trip_purpose   or "[]"))
            candidate_all      = candidate_place | candidate_activity | candidate_purpose
 
            # Jaccard similarity
            if not source_all and not candidate_all:
                similarity = 0.0
            else:
                intersection = len(source_all & candidate_all)
                union        = len(source_all | candidate_all)
                similarity   = round(intersection / union, 3) if union > 0 else 0.0
 
            if similarity > 0:
                scored.append({
                    "package_id":      package.package_id,
                    "package_name":    package.package_name,
                    "country":         package.country,
                    "state":           package.state,
                    "no_of_days":      package.no_of_days,
                    "total_price":     package.total_price,
                    "place_types":     list(candidate_place),
                    "activity_tags":   list(candidate_activity),
                    "duration_type":   tags.duration_type,
                    "budget_category": tags.budget_category,
                    "similarity":      similarity,
                })
 
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]
 
    finally:
        db.close()
 
 

# GET TRENDING PACKAGES
# Based on booking count in our booking_history
 
def get_trending_packages(limit: int = 10) -> list[dict]:
    db = get_db()
    try:
        # Count bookings per package
        booking_counts = (
            db.query(
                BookingHistory.package_id,
                func.count(BookingHistory.booking_id).label("booking_count")
            )
            .filter(BookingHistory.booking_status != "CANCELLED")
            .group_by(BookingHistory.package_id)
            .order_by(func.count(BookingHistory.booking_id).desc())
            .limit(limit)
            .all()
        )
 
        trending = []
        for row in booking_counts:
            package = db.query(PackageCache).filter(
                PackageCache.package_id == row.package_id,
                PackageCache.package_status == "TRUE"
            ).first()
 
            if not package:
                continue
 
            tags = db.query(PackageTags).filter(
                PackageTags.package_id == row.package_id
            ).first()
 
            trending.append({
                "package_id":      package.package_id,
                "package_name":    package.package_name,
                "country":         package.country,
                "state":           package.state,
                "no_of_days":      package.no_of_days,
                "total_price":     package.total_price,
                "booking_count":   row.booking_count,
                "place_types":     json.loads(tags.place_types    or "[]") if tags else [],
                "activity_tags":   json.loads(tags.activity_tags  or "[]") if tags else [],
                "duration_type":   tags.duration_type   if tags else None,
                "budget_category": tags.budget_category if tags else None,
            })
 
        return trending
 
    finally:
        db.close()
 
 

# INTERNAL HELPER

 
def _get_profile(user_id: int, db: Session) -> dict | None:
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
    
# FULL PACKAGE RECOMMENDATIONS WITH RAW JAVA API RESPONSE INCLUDED

def get_recommended_packages_full(user_id: int, limit: int = 10) -> list[dict]:
    db = get_db()
    try:
        profile     = _get_profile(user_id, db)
        preferences = get_user_preferences(user_id, db)

        all_tags = db.query(PackageTags).all()
        scored   = []

        for tags in all_tags:
            package = db.query(PackageCache).filter(
                PackageCache.package_id == tags.package_id,
                PackageCache.package_status == "TRUE"
            ).first()

            if not package:
                continue

            score = score_package(tags, profile, preferences)
            raw   = json.loads(package.raw_json or "{}")

            scored.append({
                # Recommendation metadata
                "score":           score,
                "place_types":     json.loads(tags.place_types    or "[]"),
                "activity_tags":   json.loads(tags.activity_tags  or "[]"),
                "season_tags":     json.loads(tags.season_tags    or "[]"),
                "duration_type":   tags.duration_type,
                "budget_category": tags.budget_category,

                # Full package object exactly as Java API returns
                "packageId":               raw.get("packageId"),
                "packageName":             raw.get("packageName"),
                "country":                 raw.get("country"),
                "state":                   raw.get("state"),
                "noOfDays":                raw.get("noOfDays"),
                "totalPrice":              raw.get("totalPrice"),
                "packageStatus":           raw.get("packageStatus"),
                "packageImageUrl":         raw.get("packageImageUrl", []),
                "packageActivities":       raw.get("packageActivities", []),
                "packageDiscountedAmount": raw.get("packageDiscountedAmount"),
                "currency":                raw.get("currency"),
                "vendor":                  raw.get("vendor"),
                "createdDate":             raw.get("createdDate"),
                "modifiedDate":            raw.get("modifiedDate"),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    finally:
        db.close()
        
def get_similar_packages_full(package_id: int, limit: int = 6) -> list[dict]:
    db = get_db()
    try:
        source_tags = db.query(PackageTags).filter(
            PackageTags.package_id == package_id
        ).first()

        if not source_tags:
            return []

        source_place    = set(json.loads(source_tags.place_types    or "[]"))
        source_activity = set(json.loads(source_tags.activity_tags  or "[]"))
        source_purpose  = set(json.loads(source_tags.trip_purpose   or "[]"))
        source_all      = source_place | source_activity | source_purpose

        all_tags = db.query(PackageTags).filter(
            PackageTags.package_id != package_id
        ).all()

        scored = []

        for tags in all_tags:
            package = db.query(PackageCache).filter(
                PackageCache.package_id == tags.package_id,
                PackageCache.package_status == "TRUE"
            ).first()

            if not package:
                continue

            candidate_place    = set(json.loads(tags.place_types    or "[]"))
            candidate_activity = set(json.loads(tags.activity_tags  or "[]"))
            candidate_purpose  = set(json.loads(tags.trip_purpose   or "[]"))
            candidate_all      = candidate_place | candidate_activity | candidate_purpose

            if not source_all and not candidate_all:
                similarity = 0.0
            else:
                intersection = len(source_all & candidate_all)
                union        = len(source_all | candidate_all)
                similarity   = round(intersection / union, 3) if union > 0 else 0.0

            if similarity > 0:
                raw = json.loads(package.raw_json or "{}")
                scored.append({
                    # Similarity metadata
                    "similarity":      similarity,
                    "place_types":     list(candidate_place),
                    "activity_tags":   list(candidate_activity),
                    "duration_type":   tags.duration_type,
                    "budget_category": tags.budget_category,

                    # Full package object
                    "packageId":               raw.get("packageId"),
                    "packageName":             raw.get("packageName"),
                    "country":                 raw.get("country"),
                    "state":                   raw.get("state"),
                    "noOfDays":                raw.get("noOfDays"),
                    "totalPrice":              raw.get("totalPrice"),
                    "packageStatus":           raw.get("packageStatus"),
                    "packageImageUrl":         raw.get("packageImageUrl", []),
                    "packageActivities":       raw.get("packageActivities", []),
                    "packageDiscountedAmount": raw.get("packageDiscountedAmount"),
                    "currency":                raw.get("currency"),
                    "vendor":                  raw.get("vendor"),
                    "createdDate":             raw.get("createdDate"),
                    "modifiedDate":            raw.get("modifiedDate"),
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]

    finally:
        db.close()


def get_trending_packages_full(limit: int = 10) -> list[dict]:
    db = get_db()
    try:
        from app.models.booking import BookingHistory
        from sqlalchemy import func

        booking_counts = (
            db.query(
                BookingHistory.package_id,
                func.count(BookingHistory.booking_id).label("booking_count")
            )
            .filter(BookingHistory.booking_status != "CANCELLED")
            .group_by(BookingHistory.package_id)
            .order_by(func.count(BookingHistory.booking_id).desc())
            .limit(limit)
            .all()
        )

        trending = []
        for row in booking_counts:
            package = db.query(PackageCache).filter(
                PackageCache.package_id == row.package_id,
                PackageCache.package_status == "TRUE"
            ).first()

            if not package:
                continue

            tags = db.query(PackageTags).filter(
                PackageTags.package_id == row.package_id
            ).first()

            raw = json.loads(package.raw_json or "{}")

            trending.append({
                # Trending metadata
                "booking_count":   row.booking_count,
                "place_types":     json.loads(tags.place_types    or "[]") if tags else [],
                "activity_tags":   json.loads(tags.activity_tags  or "[]") if tags else [],
                "duration_type":   tags.duration_type   if tags else None,
                "budget_category": tags.budget_category if tags else None,

                # Full package object
                "packageId":               raw.get("packageId"),
                "packageName":             raw.get("packageName"),
                "country":                 raw.get("country"),
                "state":                   raw.get("state"),
                "noOfDays":                raw.get("noOfDays"),
                "totalPrice":              raw.get("totalPrice"),
                "packageStatus":           raw.get("packageStatus"),
                "packageImageUrl":         raw.get("packageImageUrl", []),
                "packageActivities":       raw.get("packageActivities", []),
                "packageDiscountedAmount": raw.get("packageDiscountedAmount"),
                "currency":                raw.get("currency"),
                "vendor":                  raw.get("vendor"),
                "createdDate":             raw.get("createdDate"),
                "modifiedDate":            raw.get("modifiedDate"),
            })

        return trending

    finally:
        db.close()
        
