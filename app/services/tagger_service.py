import json
from datetime import datetime
from keybert import KeyBERT
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.package import PackageCache, PackageTags
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
kw_model: KeyBERT | None = None

def log(msg:str):
    print(f"[TAGGER {datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_db() -> Session:
    return SessionLocal()

def get_keyword_model() -> KeyBERT:
    global kw_model

    if kw_model is None:
        log(f"Loading keyword model: {MODEL_NAME}")
        sentence_model = SentenceTransformer(MODEL_NAME)
        kw_model = KeyBERT(model=sentence_model)
        log("Keyword model loaded.")

    return kw_model


# KEYWORD -> TAG MAPPINGS

PLACE_TYPE_KEYWORDS = {
    "beach":      ["beach", "coastal", "sea", "ocean", "shore", "sand", "waves"],
    "mountain":   ["mountain", "hill", "peak", "summit", "altitude", "valley", "highland"],
    "island":     ["island", "archipelago"],
    "snow":       ["snow", "glacier", "ice", "frozen", "snowfall"],
    "forest":     ["forest", "jungle", "wildlife", "woods", "nature"],
    "desert":     ["desert", "dunes", "arid"],
    "religious":  ["temple", "religious", "spiritual", "pilgrimage", "darshan",
                   "mata", "mandir", "mosque", "church", "shrine", "sacred"],
    "historical": ["fort", "historical", "heritage", "monument", "museum",
                   "ruins", "ancient", "palace", "castle", "balancing rock"],
    "urban":      ["city", "urban", "market", "bazaar", "street", "food",
                   "nightlife", "shopping", "restaurant"],
    "waterpark":  ["waterpark", "water park", "slides", "pool", "aqua"],
    "nature":     ["nature", "eco", "green", "scenic", "landscape", "wilderness"],
    
    }


ACTIVITY_TAG_KEYWORDS = {
    "hiking":         ["hiking", "hike", "trail", "trek", "walk", "path"],
    "trekking":       ["trekking", "trek", "expedition", "mountaineering"],
    "swimming":       ["swimming", "swim", "pool", "water"],
    "camping":        ["camping", "camp", "tent", "bonfire", "overnight"],
    "cycling":        ["cycling", "cycle", "bike", "bicycle"],
    "scuba_diving":   ["scuba", "diving", "dive", "underwater", "coral"],
    "snorkeling":     ["snorkeling", "snorkel", "reef"],
    "kayaking":       ["kayaking", "kayak", "paddle", "rowing"],
    "paragliding":    ["paragliding", "paraglide", "gliding", "flying", "sky"],
    "mountaineering": ["mountaineering", "climbing", "summit", "peak", "ascent"],
    "adventure":      ["adventure", "thrill", "extreme", "adrenaline"],
    "water_sports":   ["water sports", "rafting", "surfing", "jet ski", "boat"],
    "wildlife":       ["wildlife", "safari", "jungle", "animals", "birds"],
    "sightseeing":    ["sightseeing", "tourist", "visit", "explore", "landmark", "gem", "hidden"],
    "food_tour":      ["food", "cuisine", "restaurant", "eating", "dukan", "street food"],
    "religious":      ["darshan", "puja", "prayer", "temple", "pilgrimage", "spiritual"],
    "welness":        ["welness", "spa", "yoga", "meditation", "ayurvedic", "retreat", "healing"],
    "nightlife":      ["nightlife", "pub", "bar", "club", "party", "drinks", "crawl"],
}


TRIP_PURPOSE_KEYWORDS = {
    "honeymoon": ["honeymoon", "romantic", "couple", "romance", "anniversary"],
    "family":    ["family", "children", "kids", "child", "infant", "parents"],
    "friends":   ["friends", "group", "gang", "crew", "buddy"],
    "adventure": ["adventure", "thrill", "extreme", "adrenaline", "challenge"],
    "solo":      ["solo", "alone", "backpacker", "independent"],
    "luxury":    ["luxury", "premium", "exclusive", "elite", "lavish"],
    "religious": ["religious", "pilgrimage", "spiritual", "devotion", "darshan"],
    "cultural":  ["cultural", "heritage", "history", "art", "traditional"],
}

# Direct map from activityCategory API field
CATEGORY_TO_ACTIVITY_TAG = {
    # Adventure
    "Trekking & Hiking":               ["trekking", "hiking", "adventure"],
    "Camping":                         ["camping"],
    "Paragliding & Skydiving":         ["paragliding", "adventure"],
    "Mountaineering & Rock Climbing":  ["mountaineering", "trekking", "adventure"],
    "Cycling & Biking Tours":          ["cycling"],
    "Ziplining & Bungee Jumping":      ["adventure"],
    
    # Water Sports
    "Scuba Diving & Snorkeling":       ["scuba_diving", "snorkeling", "water_sports"],
    "Kayaking & Canoeing":             ["kayaking", "water_sports"],
    "White Water Rafting":             ["water_sports", "adventure"],
    "Jet Skiing & Parasailing":        ["water_sports", "adventure"],
    "Surfing & Windsurfing":           ["water_sports", "adventure"],
    "Cruises & Houseboat Stays":       ["water_sports"],

    # Cultural & Historical
    "Monument & Heritage Tours":       ["sightseeing", "historical", "cultural"],
    "Day City Tours":                  ["sightseeing", "urban"],
    "Museums & Art Galleries":         ["historical", "cultural"],
    "Religious & Pilgrim Tours":       ["religious"],
    "Walking & Photography Tours":     ["sightseeing", "cultural"],

    # Nature & Wildlife
    "Jungle Safari":                   ["wildlife", "adventure", "forest"],
    "Bird Watching Tours":             ["wildlife", "nature"],
    "Nature Walks & Eco Tours":        ["nature", "hiking"],
    "Camping & Glamping":              ["camping"],

    # Entertainment & Leisure
    "Theme & Water Parks":             ["waterpark"],
    "Cultural Shows & Dance Performances": ["cultural"],
    "Food Walks & Cooking Classes":    ["food_tour"],
    "Wine Tasting Tours":              ["food_tour", "luxury"],
    "Nightlife & Pub Crawls":          ["nightlife", "urban"],

    # Wellness
    "Spa & Ayurvedic Massages":        ["wellness", "luxury"],
    "Yoga & Meditation Retreats":      ["wellness", "religious"],
    "Hot Springs & Wellness Stays":    ["wellness"],
}
 
# Direct map from bestTimeToVisit API field
SEASON_MAPPING = {
    "Summer":     "summer",
    "Winter":     "winter",
    "Monsoon":    "monsoon",
    "Spring":     "spring",
    "Autumn":     "autumn",
    "Pre-Winter": "winter",
    "Rainy":      "monsoon",
}


# BUILD TEXT FROM raw_json

def build_package_text(package: PackageCache) -> tuple[str, list[str], list[str]]:
    raw = json.loads(package.raw_json or "{}")

    parts = [
        package.package_name or "",
        f"Country {package.country}" if package.country else "",
        f"State {package.state}" if package.state else "",
    ]

    categories = []
    best_times  = []

    for pa in raw.get("packageActivities", []):
        activity = pa.get("activity") or {}

        name      = activity.get("activityName", "")
        desc      = activity.get("description", "")
        category  = activity.get("activityCategory", "")
        best_time = activity.get("bestTimeToVisit", "")
        state     = activity.get("state", "")
        address   = activity.get("address", "")

        # Always add structured fields — language independent
        parts += [name, category, best_time, state, address]

        # Only add description if English — Hindi breaks KeyBERT
        if desc and desc.isascii():
            parts.append(desc)

        if category:
            categories.append(category)
        if best_time:
            best_times.append(best_time)

    # Add debug log temporarily
    text = " ".join(filter(None, parts))
    log(f"  categories found: {categories}")
    log(f"  best_times found: {best_times}")
    log(f"  text preview: {text[:120]}")

    return text, categories, best_times
# MATCH KEYWORDS -> TAGS

def match_keywords_to_tags(keywords: list[str], mapping: dict) -> list[str]:
    matched = set()
    kw_lower = [k.lower() for k in keywords]
    
    for tag , trigger_words in mapping.items():
        for trigger in trigger_words:
            for kw in kw_lower:
                if trigger in kw or kw in trigger:
                    matched.add(tag)
                    break
    return list(matched)

def infer_budget(price: float) -> str:
    if price <= 5000:
        return "budget"
    elif price <= 20000:
        return "mid_range"
    return "luxury"


def infer_duration(days: int) -> str:
    if days <=3:
        return "short_trip"
    elif days <=6:
        return "medium_trip"
    return "long_trip"



# TAG ONE PACKAGE 

def tag_package(package: PackageCache) -> dict:
    text, categories, best_times = build_package_text(package)
    keyword_model = get_keyword_model()

    # KeyBERT keyword extraction
    raw_kwywords = keyword_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=15
    )
    keywords = [kw for kw, score in raw_kwywords]
    
    # NLP based tag matching
    
    place_types = set(match_keywords_to_tags(keywords, PLACE_TYPE_KEYWORDS))
    activity_tags = set(match_keywords_to_tags(keywords, ACTIVITY_TAG_KEYWORDS))
    trip_purpose = set(match_keywords_to_tags(keywords, TRIP_PURPOSE_KEYWORDS))
    season_tags = set()
    
    # Direct tag additions from structured API fields
    
    for category in categories:
        if category in CATEGORY_TO_ACTIVITY_TAG:
            activity_tags.update(CATEGORY_TO_ACTIVITY_TAG[category])
            
    for best_time in best_times:
        if best_time in SEASON_MAPPING:
            season_tags.add(SEASON_MAPPING[best_time])
            
    return {
        "place_types":     list(place_types),
        "activity_tags":   list(activity_tags),
        "trip_purpose":    list(trip_purpose),
        "season_tags":     list(season_tags),
        "duration_type":   infer_duration(package.no_of_days or 0),
        "budget_category": infer_budget(package.total_price or 0),
    }
    
    
# TAG ALL PACKAGES

def run_tagger() -> dict:
    log("TAGGER STARTED")
    db = get_db()
    tagged_count = 0
    failed_count = 0

    try:
        get_keyword_model()

        packages = db.query(PackageCache).filter(
            PackageCache.package_status == "TRUE"
        ).all()
        
        for package in packages:
            try:
                tags = tag_package(package)
                existing = db.query(PackageTags).filter(
                    PackageTags.package_id == package.package_id
                ).first()
                
                if existing:
                    existing.place_types     = json.dumps(tags["place_types"])
                    existing.activity_tags   = json.dumps(tags["activity_tags"])
                    existing.trip_purpose    = json.dumps(tags["trip_purpose"])
                    existing.season_tags     = json.dumps(tags["season_tags"])
                    existing.duration_type   = tags["duration_type"]
                    existing.budget_category = tags["budget_category"]
                    existing.tagged_at       = datetime.now()
                    
                else:
                    db.add(PackageTags(
                        package_id      = package.package_id,
                        place_types     = json.dumps(tags["place_types"]),
                        activity_tags   = json.dumps(tags["activity_tags"]),
                        trip_purpose    = json.dumps(tags["trip_purpose"]),
                        season_tags     = json.dumps(tags["season_tags"]),
                        duration_type   = tags["duration_type"],
                        budget_category = tags["budget_category"],
                        tagged_at       = datetime.now()
                    ))     
                    
                db.commit()
                tagged_count += 1
                log(f"Package {package.package_id} | {package.package_name}")
                log(f"  place_types:   {tags['place_types']}")
                log(f"  activity_tags: {tags['activity_tags']}")
                log(f"  trip_purpose:  {tags['trip_purpose']}")
                log(f"  season_tags:   {tags['season_tags']}")
                log(f"  duration:      {tags['duration_type']}")
                log(f"  budget:        {tags['budget_category']}")

            except Exception as e:
                db.rollback()
                failed_count += 1
                log(f"Package {package.package_id} tagging failed: {e}")
    
    except Exception as e:
        db.rollback()
        msg = f"Tagger Error: {e}"
        log(msg)
        return {"success": False, "message": msg}

    finally:
        db.close()

    msg = f"Tagger done - {tagged_count} tagged, {failed_count} failed."
    log(msg)
    return {
        "success": failed_count == 0,
        "message": msg,
        "tagged_count": tagged_count,
        "failed_count": failed_count,
    } 
