from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.services.companion_core.schemas import EmotionalMemoryRecord


class EmotionalMemoryStore:
    def append(self, record: EmotionalMemoryRecord) -> None:
        raise NotImplementedError

    def list_recent(self, user_id: str, days: int = 7) -> list[EmotionalMemoryRecord]:
        raise NotImplementedError

    def clear(self, user_id: str | None = None) -> None:
        raise NotImplementedError


class NoOpEmotionalMemoryStore(EmotionalMemoryStore):
    def append(self, record: EmotionalMemoryRecord) -> None:
        del record

    def list_recent(self, user_id: str, days: int = 7) -> list[EmotionalMemoryRecord]:
        del user_id
        del days
        return []

    def clear(self, user_id: str | None = None) -> None:
        del user_id


class InMemoryEmotionalMemoryStore(EmotionalMemoryStore):
    def __init__(self) -> None:
        self._lock = Lock()
        self._records: dict[str, list[EmotionalMemoryRecord]] = defaultdict(list)

    def append(self, record: EmotionalMemoryRecord) -> None:
        with self._lock:
            self._records[record.user_id].append(record)

    def list_recent(self, user_id: str, days: int = 7) -> list[EmotionalMemoryRecord]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with self._lock:
            return [record for record in self._records.get(user_id, []) if record.timestamp >= cutoff]

    def clear(self, user_id: str | None = None) -> None:
        with self._lock:
            if user_id is None:
                self._records.clear()
            else:
                self._records.pop(user_id, None)


_demo_memory_store = InMemoryEmotionalMemoryStore()
_noop_memory_store = NoOpEmotionalMemoryStore()


def get_demo_memory_store() -> EmotionalMemoryStore:
    return _demo_memory_store


def get_noop_memory_store() -> EmotionalMemoryStore:
    return _noop_memory_store
