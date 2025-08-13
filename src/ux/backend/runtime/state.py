from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional

from ..schemas import Event, SessionSummary


@dataclass
class Subscriber:
    queue: "asyncio.Queue[Event]" = field(default_factory=asyncio.Queue)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: List[Subscriber] = []
        self._lock = asyncio.Lock()
        self._trace: List[Event] = []
        self._latest_session: Optional[SessionSummary] = None

    @property
    def trace(self) -> List[Event]:
        return list(self._trace)

    @property
    def latest_session(self) -> Optional[SessionSummary]:
        return self._latest_session

    def set_latest_session(self, session: SessionSummary) -> None:
        self._latest_session = session

    async def publish(self, event: Event) -> None:
        # Backfill timestamp
        if event.ts_ms is None:
            event.ts_ms = int(time.time() * 1000)
        self._trace.append(event)
        async with self._lock:
            for sub in self._subscribers:
                await sub.queue.put(event)

    async def subscribe(self) -> AsyncIterator[Event]:
        sub = Subscriber()
        async with self._lock:
            self._subscribers.append(sub)
        try:
            while True:
                event = await sub.queue.get()
                yield event
        finally:
            async with self._lock:
                if sub in self._subscribers:
                    self._subscribers.remove(sub)


# Global singleton for dev
bus = EventBus()
