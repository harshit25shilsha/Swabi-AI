from apscheduler.schedulers.background import BackgroundScheduler
from app.core.pipeline import run_pipeline, run_events_pipeline

scheduler = BackgroundScheduler()
_started = False


def start_scheduler():
    global _started

    if _started and scheduler.running:
        return
    # full pipeline every 3 hours
    # sync packages/activities/users/bookings/preferences -> tag -> profile
    scheduler.add_job(
        lambda: run_pipeline("SCHEDULER"),
        trigger="interval",
        hours=3,
        id="full_pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    
    # Events pipeline every 30 minutes
    # sync view + search events -> update profiles
    
    scheduler.add_job(
        lambda:run_events_pipeline("EVENTS SCHEDULER"),
        trigger = "interval",
        minutes = 30,
        id = "events_pipeline",
        replace_existing = True,
        max_instances = 1,
        coalesce = True,
    )
    
    scheduler.start()
    _started = True
    print("[SCHEDULER] Started - full pipeline runs every 3 hours, events 30min.")


def stop_scheduler():
    global _started

    if _started and scheduler.running:
        scheduler.shutdown()
        _started = False
        print("[SCHEDULER] Stopped.")
