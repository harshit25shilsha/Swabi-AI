# app/scheduler/jobs.py
from apscheduler.schedulers.background import BackgroundScheduler

from app.services.sync_service import run_full_sync

scheduler = BackgroundScheduler()
_started = False


def start_scheduler():
    global _started

    if _started and scheduler.running:
        return

    scheduler.add_job(
        run_full_sync,
        trigger="interval",
        hours=3,
        id="full_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _started = True
    print("[SCHEDULER] Started - sync runs every 3 hours.")


def stop_scheduler():
    global _started

    if _started and scheduler.running:
        scheduler.shutdown()
        _started = False
        print("[SCHEDULER] Stopped.")
