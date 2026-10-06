from collections import deque
from threading import Lock

from .models import InfrastructurePlan

_MAX_HISTORY = 25
_history: deque[InfrastructurePlan] = deque(maxlen=_MAX_HISTORY)
_lock = Lock()


def record_plan(plan: InfrastructurePlan) -> None:
    with _lock:
        _history.append(plan)


def list_plans() -> list[InfrastructurePlan]:
    with _lock:
        return list(reversed(_history))
