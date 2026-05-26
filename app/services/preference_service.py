import json
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.preference import UserPreference

# Map Preference Fields to Our Tag System

# Maps preference activity_types to our activity_tags


PREF_ACTIVITY_MAP = {
    "Trekking & Hiking":              ["trekking", "hiking", "adventure"],
    "Camping":                        ["camping"],
    "Paragliding & Skydiving":        ["paragliding", "adventure"],
    "Mountaineering & Rock Climbing": ["mountaineering", "trekking", "adventure"],
    "Cycling & Biking Tours":         ["cycling"],
    "Ziplining & Bungee Jumping":     ["adventure"],
    "Scuba Diving & Snorkeling":      ["scuba_diving", "snorkeling", "water_sports"],
    "Kayaking & Canoeing":            ["kayaking", "water_sports"],
    "White Water Rafting":            ["water_sports", "adventure"],
    "Jet Skiing & Parasailing":       ["water_sports", "adventure"],
    "Surfing & Windsurfing":          ["water_sports", "adventure"],
    "Cruises & Houseboat Stays":      ["water_sports"],
    "Monument & Heritage Tours":      ["sightseeing", "historical", "cultural"],
    "Day City Tours":                 ["sightseeing", "urban"],
    "Museums & Art Galleries":        ["historical", "cultural"],
    "Religious & Pilgrim Tours":      ["religious"],
    "Walking & Photography Tours":    ["sightseeing", "cultural"],
    "Jungle Safari":                  ["wildlife", "adventure"],
    "Bird Watching Tours":            ["wildlife"],
    "Nature Walks & Eco Tours":       ["nature", "hiking"],
    "Camping & Glamping":             ["camping"],
    "Theme & Water Parks":            ["waterpark"],
    "Cultural Shows & Dance Performances": ["cultural"],
    "Food Walks & Cooking Classes":   ["food_tour"],
    "Wine Tasting Tours":             ["food_tour", "luxury"],
    "Nightlife & Pub Crawls":         ["nightlife", "urban"],
    "Spa & Ayurvedic Massages":       ["wellness", "luxury"],
    "Yoga & Meditation Retreats":     ["wellness"],
    "Hot Springs & Wellness Stays":   ["wellness"],
    # Preferences API simpler names
    "Hiking":                         ["hiking", "trekking"],
    "Shopping":                       ["urban"],
    "Food Tours":                     ["food_tour"],
    "Nightlife":                      ["nightlife", "urban"],
    "Cultural Tours":                 ["cultural", "sightseeing"],
}

# Maps preference place_types to our place tag system
PREF_PLACE_MAP = {
    "Beach":       "beach",
    "Mountain":    "mountain",
    "Island":      "island",
    "Countryside": "nature",
    "Forest":      "forest",
    "Desert":      "desert",
    "City":        "urban",
    "Snow":        "snow",
}

# Maps preference trip_purposes to our purpose tags
PREF_PURPOSE_MAP = {
    "Honeymoon":    "honeymoon",
    "Solo Trip":    "solo",
    "Friends Trip": "friends",
    "Family Trip":  "family",
    "Adventure":    "adventure",
    "Cultural":     "cultural",
    "Religious":    "religious",
    "Luxury":       "luxury",
}

# Maps preference season to our season tags
PREF_SEASON_MAP = {
    "Summer":     "summer",
    "Winter":     "winter",
    "Spring":     "spring",
    "Autumn":     "autumn",
    "Monsoon":    "monsoon",
}


# Maps preference trip_duration to our duration_type
PREF_DURATION_MAP = {
    "Short Trip (1-3 days)":   "short_trip",
    "Medium Trip (4-7 days)":  "medium_trip",
    "Long Trip (7+ days)":     "long_trip",
}


# GET MAPPED PREFERENCES FOR ONE USER 


def get_user_preferences(user_id: int, db: Session) -> dict | None:
    pref = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
 
    if not pref:
        return None
 
    activity_types = json.loads(pref.activity_types or "[]")
    place_types    = json.loads(pref.place_types    or "[]")
    season         = json.loads(pref.season         or "[]")
    trip_purposes  = json.loads(pref.trip_purposes  or "[]")
    trip_duration  = json.loads(pref.trip_duration  or "[]")
 
    # Map activity_types → activity tags
    mapped_activities = set()
    for activity in activity_types:
        tags = PREF_ACTIVITY_MAP.get(activity, [])
        mapped_activities.update(tags)
 
    # Map place_types → place tags
    mapped_places = set()
    for place in place_types:
        tag = PREF_PLACE_MAP.get(place)
        if tag:
            mapped_places.add(tag)
 
    # Map trip_purposes → purpose tags
    mapped_purposes = set()
    for purpose in trip_purposes:
        tag = PREF_PURPOSE_MAP.get(purpose)
        if tag:
            mapped_purposes.add(tag)
 
    # Map season → season tags
    mapped_seasons = set()
    for s in season:
        tag = PREF_SEASON_MAP.get(s)
        if tag:
            mapped_seasons.add(tag)
 
    # Map trip_duration → preferred duration type
    mapped_durations = set()
    for d in trip_duration:
        tag = PREF_DURATION_MAP.get(d)
        if tag:
            mapped_durations.add(tag)
 
    return {
        "activity_tags":  list(mapped_activities),
        "place_types":    list(mapped_places),
        "trip_purpose":   list(mapped_purposes),
        "season_tags":    list(mapped_seasons),
        "duration_types": list(mapped_durations),
    }