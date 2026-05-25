# app/scheduler/jobs.py
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.tagger_service import run_tagger
from app.services.sync_service import run_full_sync
from app.services.profile_service import run_profiler

scheduler = BackgroundScheduler()
_started = False

def sync_tag_profile():
    run_full_sync()
    run_tagger()
    run_profiler()


def start_scheduler():
    global _started

    if _started and scheduler.running:
        return

    scheduler.add_job(
        sync_tag_profile,
        trigger="interval",
        hours=3,
        id="full_pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _started = True
    print("[SCHEDULER] Started - sync + profile runs every 3 hours.")


def stop_scheduler():
    global _started

    if _started and scheduler.running:
        scheduler.shutdown()
        _started = False
        print("[SCHEDULER] Stopped.")
