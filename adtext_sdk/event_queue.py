import asyncio
import logging
import time
import uuid
from typing import List, Optional, Union
from .http import HttpClient
from .types import BatchRequest, MeasurementEvent

logger = logging.getLogger("adtext_sdk")
MAX_BATCH_SIZE = 100
FLUSH_INTERVAL_SECONDS = 5.0


class EventQueue:
    def __init__(self, http: HttpClient, sdk_version: str):
        self._http = http
        self._sdk_version = sdk_version
        self._queue: List[MeasurementEvent] = []
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

    def start(self) -> None:
        self._running = True
        self._flush_task = asyncio.ensure_future(self._flush_loop())

    async def stop(self) -> None:
        self._running = False
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self.flush()

    def enqueue(self, event: Union[MeasurementEvent, dict]) -> None:
        if isinstance(event, dict):
            event = MeasurementEvent(
                event_type=event.get("eventType", ""),
                ad_id=event.get("adId", ""),
                campaign_id=event.get("campaignId"),
                placement_id=event.get("placementId"),
                session_id=event.get("sessionId"),
                page_url=event.get("pageUrl"),
                id=event.get("id"),
                timestamp=event.get("timestamp"),
            )
        if not event.id:
            event.id = str(uuid.uuid4())
        if not event.timestamp:
            event.timestamp = int(time.time() * 1000)
        self._queue.append(event)
        if len(self._queue) >= MAX_BATCH_SIZE:
            asyncio.ensure_future(self.flush())

    async def flush(self) -> None:
        if not self._queue:
            return
        batch = self._queue[:MAX_BATCH_SIZE]
        self._queue = self._queue[MAX_BATCH_SIZE:]
        req = BatchRequest(events=batch, sdk_version=self._sdk_version)
        try:
            await self._http.post_with_retry(
                "/sdk/v1/measure/batch",
                req.to_dict(),
                max_attempts=3,
                base_delay_ms=1000.0,
            )
            logger.debug("Flushed %d events", len(batch))
        except Exception as e:
            logger.warning("Batch flush failed after retries, re-queuing %d events: %s", len(batch), e)
            self._queue[:0] = batch

    async def _flush_loop(self) -> None:
        while self._running:
            await asyncio.sleep(FLUSH_INTERVAL_SECONDS)
            await self.flush()

    @property
    def size(self) -> int:
        return len(self._queue)
