# app/services/sync_service.py
import json
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.activity import ActivityCache
from app.models.booking import BookingHistory
from app.models.package import PackageCache
from app.models.user import UserCache
from app.models.preference import UserPreference


def get_db() -> Session:
    return SessionLocal()


def log(msg: str):
    print(f"[SYNC {datetime.now().strftime('%H:%M:%S')}] {msg}")


def base_url() -> str:
    return settings.JAVA_API_BASE_URL.rstrip("/")


def safe_float(val, default=0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0) -> int:
    try:
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def sync_packages() -> dict:
    log("Starting package sync...")
    db = get_db()
    new_count = 0
    updated_count = 0

    try:
        url = (
            f"{base_url()}"
            f"/package/get_package_list_all_vendors"
            f"?pageNumber=-1&pageSize=-1&packageStatus=ALL&search=&days=&price="
        )
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        body = response.json()
        packages = body.get("data", {}).get("content", [])

        for p in packages:
            package_id = p.get("packageId")
            modified_date = str(p.get("modifiedDate", ""))

            if not package_id:
                continue

            existing = db.query(PackageCache).filter(
                PackageCache.package_id == package_id
            ).first()

            if not existing:
                db.add(
                    PackageCache(
                        package_id=package_id,
                        package_name=p.get("packageName", ""),
                        country=p.get("country", ""),
                        state=p.get("state", ""),
                        no_of_days=safe_int(p.get("noOfDays", 0)),
                        total_price=safe_float(p.get("totalPrice", 0)),
                        package_status=p.get("packageStatus", ""),
                        modified_date=modified_date,
                        raw_json=json.dumps(p),
                        last_synced_at=datetime.now(),
                    )
                )
                new_count += 1

            elif existing.modified_date != modified_date:
                existing.package_name = p.get("packageName", "")
                existing.country = p.get("country", "")
                existing.state = p.get("state", "")
                existing.no_of_days = safe_int(p.get("noOfDays", 0))
                existing.total_price = safe_float(p.get("totalPrice", 0))
                existing.package_status = p.get("packageStatus", "")
                existing.modified_date = modified_date
                existing.raw_json = json.dumps(p)
                existing.last_synced_at = datetime.now()
                updated_count += 1

        db.commit()
        msg = f"Packages done - {new_count} new, {updated_count} updated."
        log(msg)
        return {"success": True, "message": msg}

    except httpx.HTTPError as e:
        db.rollback()
        msg = f"Package sync HTTP error: {e}"
        log(msg)
        return {"success": False, "message": msg}

    except Exception as e:
        db.rollback()
        msg = f"Package sync failed: {e}"
        log(msg)
        return {"success": False, "message": msg}

    finally:
        db.close()


def sync_activities() -> dict:
    log("Starting activity sync...")
    db = get_db()
    new_count = 0
    updated_count = 0

    try:
        url = (
            f"{base_url()}"
            f"/activity/get_all_activities"
            f"?activityStatus=true&pageNumber=-1&pageSize=-1"
        )
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        activities = response.json().get("data", {}).get("content", [])

        for a in activities:
            activity_id = a.get("activityId")
            modified_date = str(a.get("modifiedDate", ""))

            if not activity_id:
                continue

            existing = db.query(ActivityCache).filter(
                ActivityCache.activity_id == activity_id
            ).first()

            if not existing:
                db.add(
                    ActivityCache(
                        activity_id=activity_id,
                        activity_name=a.get("activityName", ""),
                        description=a.get("description", ""),
                        category=a.get("activityCategory", ""),
                        best_time=a.get("bestTimeToVisit", ""),
                        country=a.get("country", ""),
                        state=a.get("state", ""),
                        price=safe_float(a.get("activityPrice", 0)),
                        modified_date=modified_date,
                        last_synced_at=datetime.now(),
                    )
                )
                new_count += 1

            elif existing.modified_date != modified_date:
                existing.activity_name = a.get("activityName", "")
                existing.description = a.get("description", "")
                existing.category = a.get("activityCategory", "")
                existing.best_time = a.get("bestTimeToVisit", "")
                existing.country = a.get("country", "")
                existing.state = a.get("state", "")
                existing.price = safe_float(a.get("activityPrice", 0))
                existing.modified_date = modified_date
                existing.last_synced_at = datetime.now()
                updated_count += 1

        db.commit()
        msg = f"Activities done - {new_count} new, {updated_count} updated."
        log(msg)
        return {"success": True, "message": msg}

    except httpx.HTTPError as e:
        db.rollback()
        msg = f"Activity sync HTTP error: {e}"
        log(msg)
        return {"success": False, "message": msg}

    except Exception as e:
        db.rollback()
        msg = f"Activity sync failed: {e}"
        log(msg)
        return {"success": False, "message": msg}

    finally:
        db.close()


def sync_users() -> dict:
    log("Starting user sync...")
    db = get_db()
    new_count = 0
    updated_count = 0

    try:
        url = (
            f"{base_url()}"
            f"/user/get_user_list"
            f"?pageNumber=-1&pageSize=-1&search=&status=all&sortBy=&sortDirection=asc"
        )
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        users = response.json().get("data", {}).get("content", [])

        for u in users:
            user_id = u.get("userId")
            if not user_id:
                continue

            existing = db.query(UserCache).filter(
                UserCache.user_id == user_id
            ).first()

            if not existing:
                db.add(
                    UserCache(
                        user_id=user_id,
                        first_name=u.get("firstName", ""),
                        last_name=u.get("lastName", ""),
                        country=u.get("country", ""),
                        state=u.get("state", ""),
                        gender=u.get("gender", ""),
                        last_synced_at=datetime.now(),
                    )
                )
                new_count += 1
            else:
                first_name = u.get("firstName", "")
                last_name = u.get("lastName", "")
                country = u.get("country", "")
                state = u.get("state", "")
                gender = u.get("gender", "")

                if (
                    existing.first_name != first_name
                    or existing.last_name != last_name
                    or existing.country != country
                    or existing.state != state
                    or existing.gender != gender
                ):
                    existing.first_name = first_name
                    existing.last_name = last_name
                    existing.country = country
                    existing.state = state
                    existing.gender = gender
                    existing.last_synced_at = datetime.now()
                    updated_count += 1

        db.commit()
        msg = f"Users done - {new_count} new, {updated_count} updated."
        log(msg)
        return {"success": True, "message": msg}

    except httpx.HTTPError as e:
        db.rollback()
        msg = f"User sync HTTP error: {e}"
        log(msg)
        return {"success": False, "message": msg}

    except Exception as e:
        db.rollback()
        msg = f"User sync failed: {e}"
        log(msg)
        return {"success": False, "message": msg}

    finally:
        db.close()


def sync_bookings() -> dict:
    log("Starting booking sync...")
    db = get_db()
    new_count = 0
    updated_count = 0
    page = 0
    page_size = 100
    total_pages = 1

    try:
        while page < total_pages:
            url = (
                f"{base_url()}"
                f"/package_booking/get_package_booking_list_all_users"
                f"?pageNumber={page}&pageSize={page_size}"
                f"&bookingStatus=ALL&search=&sortBy=&sortDirection=asc"
            )
            response = httpx.get(url, timeout=30)
            response.raise_for_status()

            data = response.json().get("data", {})
            bookings = data.get("content", [])
            total_pages = data.get("totalPages", 1)

            for b in bookings:
                booking_id = b.get("packageBookingId")
                user_data = b.get("user") or {}
                pkg_data = b.get("pkg") or {}
                user_id = user_data.get("userId")
                package_id = pkg_data.get("packageId")

                if not booking_id or not user_id or not package_id:
                    continue

                existing = db.query(BookingHistory).filter(
                    BookingHistory.booking_id == booking_id
                ).first()

                if not existing:
                    db.add(
                        BookingHistory(
                            booking_id=booking_id,
                            user_id=user_id,
                            package_id=package_id,
                            booking_status=b.get("bookingStatus", ""),
                            booking_date=b.get("bookingDate", ""),
                            amount_paid=safe_float(b.get("totalPayableAmount", 0)),
                            num_members=safe_int(b.get("numberOfMembers", 1)),
                            synced_at=datetime.now(),
                        )
                    )
                    new_count += 1
                else:
                    booking_status = b.get("bookingStatus", "")
                    booking_date = b.get("bookingDate", "")
                    amount_paid = safe_float(b.get("totalPayableAmount", 0))
                    num_members = safe_int(b.get("numberOfMembers", 1))

                    if (
                        existing.user_id != user_id
                        or existing.package_id != package_id
                        or existing.booking_status != booking_status
                        or existing.booking_date != booking_date
                        or existing.amount_paid != amount_paid
                        or existing.num_members != num_members
                    ):
                        existing.user_id = user_id
                        existing.package_id = package_id
                        existing.booking_status = booking_status
                        existing.booking_date = booking_date
                        existing.amount_paid = amount_paid
                        existing.num_members = num_members
                        existing.synced_at = datetime.now()
                        updated_count += 1

            db.commit()
            log(f"Bookings page {page + 1}/{total_pages} done.")
            page += 1

        msg = f"Bookings done - {new_count} new, {updated_count} updated."
        log(msg)
        return {"success": True, "message": msg}

    except httpx.HTTPError as e:
        db.rollback()
        msg = f"Booking sync HTTP error: {e}"
        log(msg)
        return {"success": False, "message": msg}

    except Exception as e:
        db.rollback()
        msg = f"Booking sync failed: {e}"
        log(msg)
        return {"success": False, "message": msg}

    finally:
        db.close()


def sync_preferences() -> dict:
    log("Starting preferences sync...")
    db        = get_db()
    new_count     = 0
    updated_count = 0

    try:
        url = f"{base_url()}/travel/get_all_travel_preferences"
        response = httpx.get(url, timeout=30)
        response.raise_for_status()

        preferences = response.json()

        if not isinstance(preferences, list):
            preferences = preferences.get("data", [])

        for p in preferences:
            user_id = p.get("userId")
            if not user_id:
                continue

            existing = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).first()

            activity_types = json.dumps(p.get("activity_types", []))
            place_types    = json.dumps(p.get("place_types", []))
            season         = json.dumps(p.get("season", []))
            trip_purposes  = json.dumps(p.get("trip_purposes", []))
            trip_duration  = json.dumps(p.get("trip_duration", []))
            countries      = json.dumps(p.get("countries", []))

            if not existing:
                db.add(UserPreference(
                    user_id        = user_id,
                    activity_types = activity_types,
                    place_types    = place_types,
                    season         = season,
                    trip_purposes  = trip_purposes,
                    trip_duration  = trip_duration,
                    countries      = countries,
                ))
                new_count += 1
            else:
                existing.activity_types = activity_types
                existing.place_types    = place_types
                existing.season         = season
                existing.trip_purposes  = trip_purposes
                existing.trip_duration  = trip_duration
                existing.countries      = countries
                updated_count += 1

        db.commit()
        msg = f"Preferences done - {new_count} new, {updated_count} updated."
        log(msg)
        return {"success": True, "message": msg}

    except httpx.HTTPError as e:
        db.rollback()
        msg = f"Preferences sync HTTP error: {e}"
        log(msg)
        return {"success": False, "message": msg}

    except Exception as e:
        db.rollback()
        msg = f"Preferences sync failed: {e}"
        log(msg)
        return {"success": False, "message": msg}

    finally:
        db.close()
        




def run_full_sync() -> dict:
    log("FULL SYNC STARTED")

    results = {
        "packages": sync_packages(),
        "activities": sync_activities(),
        "users": sync_users(),
        "bookings": sync_bookings(),
        "preferences": sync_preferences(),
    }

    all_success = all(result["success"] for result in results.values())
    failed = [name for name, result in results.items() if not result["success"]]

    if all_success:
        log("FULL SYNC COMPLETED")
    else:
        log(f"FULL SYNC COMPLETED WITH FAILURES: {failed}")

    return {
        "success": all_success,
        "failed": failed,
        "results": results,
    }
