import json
import re
from datetime import datetime

from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.package import PackageCache, PackageTags

MODEL_NAME = "all-MiniLM-L6-v2"
DEBUG_TAGGER = False
kw_model: KeyBERT | None = None


def log(msg: str):
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


def normalize_text(value: str) -> str:
    value = (value or "").lower()
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def normalize_tag_list(values: set[str] | list[str]) -> list[str]:
    return sorted({value for value in values if value})


def phrase_in_text(text: str, phrase: str) -> bool:
    normalized_text = f" {normalize_text(text)} "
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return False
    return f" {normalized_phrase} " in normalized_text


# KEYWORD -> TAG MAPPINGS

PLACE_TYPE_KEYWORDS = {
    "beach": ["beach", "coastal", "sea", "ocean", "shore", "seaside", "coastline"],
    "mountain": ["mountain", "hill", "peak", "summit", "valley", "highland", "himalaya"],
    "island": ["island", "archipelago"],
    "snow": ["snow", "glacier", "ice", "frozen", "snowfall"],
    "forest": ["forest", "jungle", "wildlife sanctuary", "national park", "woods", "safari"],
    "desert": ["desert", "dunes", "arid"],
    "religious": [
        "temple",
        "religious",
        "spiritual",
        "pilgrimage",
        "darshan",
        "mata",
        "mandir",
        "mosque",
        "church",
        "shrine",
        "sacred",
    ],
    "historical": [
        "fort",
        "historical",
        "heritage",
        "monument",
        "museum",
        "ruins",
        "ancient",
        "palace",
        "castle",
        "memorial",
    ],
    "urban": ["city", "urban", "market", "bazaar", "nightlife", "shopping", "restaurant", "downtown"],
    "waterpark": ["waterpark", "water park", "slides", "aqua park", "amusement water park"],
    "nature": ["nature", "eco", "green", "scenic", "landscape", "wilderness", "countryside"],
}


ACTIVITY_TAG_KEYWORDS = {
    "hiking": ["hiking", "hike", "trail", "walking trail", "nature walk"],
    "trekking": ["trekking", "trek", "expedition", "mountaineering"],
    "swimming": ["swimming", "swim", "river swim", "lake swim", "sea swim"],
    "camping": ["camping", "camp", "tent", "bonfire", "overnight stay"],
    "cycling": ["cycling", "cycle", "bike", "bicycle"],
    "scuba_diving": ["scuba", "scuba diving", "diving", "underwater", "coral"],
    "snorkeling": ["snorkeling", "snorkel", "reef"],
    "kayaking": ["kayaking", "kayak", "paddle", "canoeing", "rowing"],
    "paragliding": ["paragliding", "paraglide", "skydiving", "parasailing"],
    "mountaineering": ["mountaineering", "rock climbing", "summit climb", "peak ascent"],
    "adventure": ["adventure", "thrill", "extreme", "adrenaline"],
    "water_sports": ["water sports", "rafting", "surfing", "jet ski", "houseboat"],
    "wildlife": ["wildlife", "safari", "bird watching", "jungle safari"],
    "sightseeing": ["sightseeing", "tourist attraction", "landmark", "guided tour", "scenic view"],
    "food_tour": ["food tour", "local cuisine", "culinary", "street food", "food walk"],
    "religious": ["darshan", "puja", "prayer", "temple", "pilgrimage", "spiritual"],
    "wellness": ["wellness", "spa", "yoga", "meditation", "ayurvedic", "retreat", "healing"],
    "nightlife": ["nightlife", "pub", "bar", "club", "party", "pub crawl"],
}


TRIP_PURPOSE_KEYWORDS = {
    "honeymoon": ["honeymoon", "romantic", "couple", "romance", "anniversary"],
    "family": ["family", "children", "kids", "child", "infant", "parents"],
    "friends": ["friends", "group", "gang", "crew", "buddy"],
    "adventure": ["adventure", "thrill", "extreme", "adrenaline", "challenge"],
    "solo": ["solo", "alone", "backpacker", "independent"],
    "luxury": ["luxury", "premium", "exclusive", "elite", "lavish"],
    "religious": ["religious", "pilgrimage", "spiritual", "devotion", "darshan"],
    "cultural": ["cultural", "heritage", "history", "art", "traditional"],
}


CATEGORY_TO_ACTIVITY_TAG = {
    "Trekking & Hiking": ["trekking", "hiking", "adventure"],
    "Camping": ["camping"],
    "Paragliding & Skydiving": ["paragliding", "adventure"],
    "Mountaineering & Rock Climbing": ["mountaineering", "trekking", "adventure"],
    "Cycling & Biking Tours": ["cycling"],
    "Ziplining & Bungee Jumping": ["adventure"],
    "Scuba Diving & Snorkeling": ["scuba_diving", "snorkeling", "water_sports"],
    "Kayaking & Canoeing": ["kayaking", "water_sports"],
    "White Water Rafting": ["water_sports", "adventure"],
    "Jet Skiing & Parasailing": ["water_sports", "adventure"],
    "Surfing & Windsurfing": ["water_sports", "adventure"],
    "Cruises & Houseboat Stays": ["water_sports"],
    "Monument & Heritage Tours": ["sightseeing", "cultural"],
    "Day City Tours": ["sightseeing"],
    "Museums & Art Galleries": ["sightseeing", "cultural"],
    "Religious & Pilgrim Tours": ["religious"],
    "Walking & Photography Tours": ["sightseeing", "cultural"],
    "Jungle Safari": ["wildlife", "adventure"],
    "Bird Watching Tours": ["wildlife"],
    "Nature Walks & Eco Tours": ["hiking"],
    "Camping & Glamping": ["camping"],
    "Theme & Water Parks": ["swimming"],
    "Cultural Shows & Dance Performances": ["cultural"],
    "Food Walks & Cooking Classes": ["food_tour"],
    "Wine Tasting Tours": ["food_tour", "luxury"],
    "Nightlife & Pub Crawls": ["nightlife"],
    "Spa & Ayurvedic Massages": ["wellness", "luxury"],
    "Yoga & Meditation Retreats": ["wellness", "religious"],
    "Hot Springs & Wellness Stays": ["wellness"],
}


CATEGORY_TO_PLACE_TAG = {
    "Trekking & Hiking": ["mountain", "nature"],
    "Camping": ["nature"],
    "Mountaineering & Rock Climbing": ["mountain"],
    "Scuba Diving & Snorkeling": ["beach"],
    "Kayaking & Canoeing": ["nature"],
    "White Water Rafting": ["nature"],
    "Jet Skiing & Parasailing": ["beach"],
    "Surfing & Windsurfing": ["beach"],
    "Cruises & Houseboat Stays": ["beach"],
    "Monument & Heritage Tours": ["historical"],
    "Day City Tours": ["urban"],
    "Museums & Art Galleries": ["historical"],
    "Religious & Pilgrim Tours": ["religious"],
    "Walking & Photography Tours": ["urban"],
    "Jungle Safari": ["forest", "nature"],
    "Bird Watching Tours": ["forest", "nature"],
    "Nature Walks & Eco Tours": ["nature"],
    "Camping & Glamping": ["nature"],
    "Theme & Water Parks": ["waterpark"],
    "Nightlife & Pub Crawls": ["urban"],
    "Spa & Ayurvedic Massages": ["nature"],
    "Yoga & Meditation Retreats": ["nature", "religious"],
    "Hot Springs & Wellness Stays": ["nature"],
}


SEASON_MAPPING = {
    "Summer": "summer",
    "Winter": "winter",
    "Monsoon": "monsoon",
    "Spring": "spring",
    "Autumn": "autumn",
    "Pre-Winter": "winter",
    "Rainy": "monsoon",
}


def build_package_text(package: PackageCache) -> tuple[str, str, list[str], list[str], list[dict]]:
    raw = json.loads(package.raw_json or "{}")

    keyword_parts = [
        package.package_name or "",
        f"Country {package.country}" if package.country else "",
        f"State {package.state}" if package.state else "",
    ]
    rule_parts = [package.package_name or "", package.country or "", package.state or ""]
    categories = []
    best_times = []
    package_activities = raw.get("packageActivities", [])

    for package_activity in package_activities:
        activity = package_activity.get("activity") or {}

        name = activity.get("activityName", "")
        desc = activity.get("description", "")
        category = activity.get("activityCategory", "")
        best_time = activity.get("bestTimeToVisit", "")
        state = activity.get("state", "")
        address = activity.get("address", "")

        keyword_parts += [name, category, best_time, state, address]
        rule_parts += [name, category, best_time, state, address, desc]

        # Keep English text for KeyBERT; use the full text separately for rules.
        if desc and desc.isascii():
            keyword_parts.append(desc)

        if category:
            categories.append(category)
        if best_time:
            best_times.append(best_time)

    keyword_text = " ".join(filter(None, keyword_parts))
    rule_text = " ".join(filter(None, rule_parts))

    if DEBUG_TAGGER:
        log(f"  categories found: {categories}")
        log(f"  best_times found: {best_times}")
        log(f"  text preview: {keyword_text[:120]}")

    return keyword_text, rule_text, categories, best_times, package_activities


def match_keywords_to_tags(keywords: list[str], mapping: dict[str, list[str]]) -> set[str]:
    matched = set()
    normalized_keywords = [normalize_text(keyword) for keyword in keywords if normalize_text(keyword)]

    for tag, trigger_words in mapping.items():
        for trigger in trigger_words:
            normalized_trigger = normalize_text(trigger)
            trigger_tokens = set(normalized_trigger.split())
            if not trigger_tokens:
                continue
            for keyword in normalized_keywords:
                keyword_tokens = set(keyword.split())
                if keyword == normalized_trigger or trigger_tokens.issubset(keyword_tokens):
                    matched.add(tag)
                    break
    return matched


def match_text_to_tags(text: str, mapping: dict[str, list[str]]) -> set[str]:
    matched = set()
    for tag, trigger_words in mapping.items():
        for trigger in trigger_words:
            if phrase_in_text(text, trigger):
                matched.add(tag)
                break
    return matched


def infer_budget(price: float) -> str:
    if price <= 5000:
        return "budget"
    if price <= 20000:
        return "mid_range"
    return "luxury"


def infer_duration(days: int) -> str:
    if days <= 3:
        return "short_trip"
    if days <= 6:
        return "medium_trip"
    return "long_trip"


def infer_trip_purpose_from_context(place_types: set[str], activity_tags: set[str], categories: list[str]) -> set[str]:
    inferred = set()
    if "Religious & Pilgrim Tours" in categories or "religious" in place_types:
        inferred.add("religious")
    if {"hiking", "trekking", "mountaineering", "paragliding", "water_sports", "adventure"}.intersection(activity_tags):
        inferred.add("adventure")
    if "historical" in place_types:
        inferred.add("cultural")
    return inferred


def refine_place_types(place_types: set[str], category_place_tags: set[str], activity_tags: set[str]) -> set[str]:
    refined = set(place_types) | set(category_place_tags)
    if {"scuba_diving", "snorkeling", "water_sports"}.intersection(activity_tags):
        refined.add("beach")
    if {"trekking", "mountaineering", "hiking"}.intersection(activity_tags):
        refined.update({"mountain", "nature"})
    if "wildlife" in activity_tags:
        refined.update({"forest", "nature"})
    return refined


def refine_activity_tags(
    activity_tags: set[str], place_types: set[str], trip_purpose: set[str], categories: list[str]
) -> set[str]:
    refined = set(activity_tags)
    if "Religious & Pilgrim Tours" in categories or "religious" in place_types:
        refined.add("religious")
    if "historical" in place_types:
        refined.add("sightseeing")
    if "waterpark" in place_types:
        refined.add("swimming")
    refined.update(trip_purpose.intersection({"adventure", "cultural", "religious"}))
    return refined


def extract_keywords(keyword_model: KeyBERT, text: str) -> list[str]:
    if not text.strip():
        return []

    raw_keywords = keyword_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=15,
    )
    return [keyword for keyword, _score in raw_keywords]


def tag_package(package: PackageCache) -> dict:
    keyword_text, rule_text, categories, best_times, package_activities = build_package_text(package)
    keyword_model = get_keyword_model()
    keywords = extract_keywords(keyword_model, keyword_text)

    place_types = match_keywords_to_tags(keywords, PLACE_TYPE_KEYWORDS) | match_text_to_tags(rule_text, PLACE_TYPE_KEYWORDS)
    activity_tags = match_keywords_to_tags(keywords, ACTIVITY_TAG_KEYWORDS) | match_text_to_tags(rule_text, ACTIVITY_TAG_KEYWORDS)
    trip_purpose = match_keywords_to_tags(keywords, TRIP_PURPOSE_KEYWORDS) | match_text_to_tags(rule_text, TRIP_PURPOSE_KEYWORDS)
    season_tags = set()
    category_place_tags = set()

    for category in categories:
        activity_tags.update(CATEGORY_TO_ACTIVITY_TAG.get(category, []))
        category_place_tags.update(CATEGORY_TO_PLACE_TAG.get(category, []))

    for best_time in best_times:
        mapped = SEASON_MAPPING.get(best_time)
        if mapped:
            season_tags.add(mapped)

    for package_activity in package_activities:
        activity = package_activity.get("activity") or {}
        for candidate in (
            activity.get("activityName", ""),
            activity.get("address", ""),
            activity.get("description", ""),
        ):
            place_types.update(match_text_to_tags(candidate, PLACE_TYPE_KEYWORDS))
            activity_tags.update(match_text_to_tags(candidate, ACTIVITY_TAG_KEYWORDS))
            trip_purpose.update(match_text_to_tags(candidate, TRIP_PURPOSE_KEYWORDS))

    place_types = refine_place_types(place_types, category_place_tags, activity_tags)
    trip_purpose.update(infer_trip_purpose_from_context(place_types, activity_tags, categories))
    activity_tags = refine_activity_tags(activity_tags, place_types, trip_purpose, categories)

    return {
        "place_types": normalize_tag_list(place_types),
        "activity_tags": normalize_tag_list(activity_tags),
        "trip_purpose": normalize_tag_list(trip_purpose),
        "season_tags": normalize_tag_list(season_tags),
        "duration_type": infer_duration(package.no_of_days or 0),
        "budget_category": infer_budget(package.total_price or 0),
    }


def run_tagger() -> dict:
    log("TAGGER STARTED")
    db = get_db()
    tagged_count = 0
    failed_count = 0

    try:
        get_keyword_model()

        packages = db.query(PackageCache).filter(PackageCache.package_status == "TRUE").all()

        for package in packages:
            try:
                tags = tag_package(package)
                existing = db.query(PackageTags).filter(PackageTags.package_id == package.package_id).first()

                if existing:
                    existing.place_types = json.dumps(tags["place_types"])
                    existing.activity_tags = json.dumps(tags["activity_tags"])
                    existing.trip_purpose = json.dumps(tags["trip_purpose"])
                    existing.season_tags = json.dumps(tags["season_tags"])
                    existing.duration_type = tags["duration_type"]
                    existing.budget_category = tags["budget_category"]
                    existing.tagged_at = datetime.now()
                else:
                    db.add(
                        PackageTags(
                            package_id=package.package_id,
                            place_types=json.dumps(tags["place_types"]),
                            activity_tags=json.dumps(tags["activity_tags"]),
                            trip_purpose=json.dumps(tags["trip_purpose"]),
                            season_tags=json.dumps(tags["season_tags"]),
                            duration_type=tags["duration_type"],
                            budget_category=tags["budget_category"],
                            tagged_at=datetime.now(),
                        )
                    )

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
        msg = f"Tagger error: {e}"
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
