import threading

from app.services.sync_service import run_full_sync, sync_preferences
from app.services.tagger_service import run_tagger
from app.services.profile_service import run_profiler

_lock = threading.Lock()


def _busy_message(label: str) -> str:
    return f"[{label}] Pipeline already running, skipping."


def run_pipeline(label: str = "PIPELINE") -> dict:
    if not _lock.acquire(blocking=False):
        msg = _busy_message(label)
        print(msg)
        return {"success": False, "message": msg}
    try:
        sync_result = run_full_sync()
        tag_result = run_tagger()
        prof_result = run_profiler()

        all_success = all(
            [
                sync_result.get("success"),
                tag_result.get("success"),
                prof_result.get("success"),
            ]
        )
        failed_steps = [
            step_name
            for step_name, step_result in (
                ("sync", sync_result),
                ("tagger", tag_result),
                ("profiler", prof_result),
            )
            if not step_result.get("success")
        ]
        message = (
            f"[{label}] Full pipeline completed successfully."
            if all_success
            else f"[{label}] Full pipeline completed with failures: {failed_steps}"
        )

        return {
            "success": all_success,
            "message": message,
            "failed_steps": failed_steps,
            "sync": sync_result,
            "tagger": tag_result,
            "profiler": prof_result,
        }
    finally:
        _lock.release()


def run_sync_only(label: str = "SYNC") -> dict:
    if not _lock.acquire(blocking=False):
        return {"success": False, "message": _busy_message(label)}
    try:
        return run_full_sync()
    finally:
        _lock.release()

def run_tagger_only() -> dict:
    if not _lock.acquire(blocking=False):
        return {"success": False, "message": _busy_message("TAGGER")}
    try:
        return run_tagger()
    finally:
        _lock.release()

def run_profiler_only() -> dict:
    if not _lock.acquire(blocking=False):
        return {"success": False, "message": _busy_message("PROFILER")}
    try:
        return run_profiler()
    finally:
        _lock.release()

def run_preferences_only() -> dict:
    if not _lock.acquire(blocking=False):
        return {"success": False, "message": _busy_message("PREFERENCES")}
    try:
        return sync_preferences()
    finally:
        _lock.release()
