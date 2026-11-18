from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Callable

log = logging.getLogger("mcp_guard.approval")


@dataclass
class ApprovalRequest:
    request_id: str
    server: str
    tool: str
    arguments: dict[str, Any]
    created_at: float
    decision: concurrent.futures.Future[bool]


class ApprovalBroker:
    """Thread-safe bridge between the asyncio proxy and desktop UI."""

    def __init__(self, loop: asyncio.AbstractEventLoop, timeout_seconds: int) -> None:
        self.loop = loop
        self.timeout_seconds = timeout_seconds
        self._lock = threading.RLock()
        self._pending: dict[str, ApprovalRequest] = {}
        self._listeners: list[Callable[[], None]] = []

    def subscribe(self, callback: Callable[[], None]) -> None:
        with self._lock:
            self._listeners.append(callback)

    def snapshot(self) -> list[ApprovalRequest]:
        with self._lock:
            return list(self._pending.values())

    def submit_decision(self, request_id: str, allowed: bool) -> bool:
        with self._lock:
            request = self._pending.pop(request_id, None)
        if request is None or request.decision.done():
            return False
        request.decision.set_result(allowed)
        self._notify()
        return True

    def _notify(self) -> None:
        with self._lock:
            listeners = list(self._listeners)
        for callback in listeners:
            try:
                callback()
            except Exception:
                log.exception("Approval UI listener failed")

    async def request_approval(
        self, server: str, tool: str, arguments: dict[str, Any]
    ) -> bool:
        request_id = uuid.uuid4().hex[:12]
        decision: concurrent.futures.Future[bool] = concurrent.futures.Future()
        request = ApprovalRequest(
            request_id, server, tool, arguments, self.loop.time(), decision
        )
        with self._lock:
            self._pending[request_id] = request
        self._notify()
        try:
            return await asyncio.wait_for(
                asyncio.wrap_future(decision), timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            log.warning("Approval timed out; blocking request %s", request_id)
            return False
        finally:
            with self._lock:
                self._pending.pop(request_id, None)
            self._notify()
