# app/scheduler/jobs.py
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from app.core.pipeline import run_pipeline

scheduler = BackgroundScheduler()
_started = False


def start_scheduler():
    global _started

    if _started and scheduler.running:
        return

    scheduler.add_job(
        lambda: run_pipeline("SCHEDULER"),
        trigger="interval",
        hours=3,
        id="full_pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _started = True
    print("[SCHEDULER] Started - full pipeline runs every 3 hours.")


def stop_scheduler():
    global _started

    if _started and scheduler.running:
        scheduler.shutdown()
        _started = False
        print("[SCHEDULER] Stopped.")
