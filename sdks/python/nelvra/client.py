import logging
import queue
import threading
import warnings
from typing import Any

import httpx

from .types import NelvraEvent

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10
_FLUSH_INTERVAL_SECONDS = 5.0
_QUEUE_MAX_SIZE = 10_000
_SEND_TIMEOUT_SECONDS = 10.0


class EventSender:
    """Drains the event queue in a background thread and POSTs to the Nelvra API."""

    def __init__(self, api_key: str, api_url: str) -> None:
        self._api_key = api_key
        self._api_url = api_url
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=_QUEUE_MAX_SIZE)
        self._thread = threading.Thread(target=self._loop, daemon=True, name="nelvra-sender")
        self._thread.start()

    def enqueue(self, event: NelvraEvent) -> None:
        try:
            self._queue.put_nowait(event.to_dict())
        except queue.Full:
            pass  # Drop silently — never block the caller's app

    def _loop(self) -> None:
        while True:
            batch: list[dict[str, Any]] = []
            try:
                event = self._queue.get(timeout=_FLUSH_INTERVAL_SECONDS)
                batch.append(event)
                while len(batch) < _BATCH_SIZE:
                    try:
                        batch.append(self._queue.get_nowait())
                    except queue.Empty:
                        break
            except queue.Empty:
                continue

            self._send(batch)

    def _send(self, events: list[dict[str, Any]]) -> None:
        try:
            resp = httpx.post(
                f"{self._api_url}/v1/events/batch",
                json={"events": events},
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=_SEND_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
        except Exception:
            warnings.warn(
                f"Nelvra: failed to send {len(events)} event(s). They have been dropped.",
                stacklevel=2,
            )


class Nelvra:
    """
    Nelvra observability client.

    Usage::

        from nelvra import Nelvra

        nelvra = Nelvra(api_key="nvl_live_...")
        nelvra.instrument()  # auto-patches openai and anthropic clients
    """

    _instance: "Nelvra | None" = None

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.nelvra.io",
        environment: str = "production",
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._api_url = api_url.rstrip("/")
        self._environment = environment
        self._sender = EventSender(api_key, self._api_url)
        self._instrumented = False
        Nelvra._instance = self

    def instrument(self) -> None:
        """Auto-patches openai and anthropic clients. Safe to call multiple times."""
        if self._instrumented:
            return

        from .instruments.openai import instrument_openai
        from .instruments.anthropic import instrument_anthropic

        instrument_openai(self._sender, self._environment)
        instrument_anthropic(self._sender, self._environment)

        self._instrumented = True

    @classmethod
    def get_instance(cls) -> "Nelvra | None":
        return cls._instance
