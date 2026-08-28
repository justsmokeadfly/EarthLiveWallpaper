import threading
import time

from application.results import UpdateResult
from application.scheduler_service import SchedulerService
from domain.enums import UpdateOutcome


def test_manual_trigger_preserves_forced_request_when_concurrent() -> None:
    calls: list[bool] = []
    done = threading.Event()

    def update(force: bool) -> UpdateResult:
        calls.append(force)
        done.set()
        return UpdateResult(UpdateOutcome.ALREADY_UP_TO_DATE, "ok")

    scheduler = SchedulerService(update)
    scheduler.start(check_interval_hours=24)
    try:
        scheduler.trigger_now(force=False)
        scheduler.trigger_now(force=True)
        assert done.wait(timeout=3)
        assert calls == [True]
    finally:
        scheduler.stop()


def test_scheduler_start_does_not_update_immediately_by_default() -> None:
    calls: list[bool] = []

    def update(force: bool) -> UpdateResult:
        calls.append(force)
        return UpdateResult(UpdateOutcome.ALREADY_UP_TO_DATE, "ok")

    scheduler = SchedulerService(update)
    scheduler.start(check_interval_hours=24)
    try:
        time.sleep(1.2)
        assert calls == []
    finally:
        scheduler.stop()
