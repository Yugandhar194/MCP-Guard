import asyncio

import pytest

from mcp_guard.approval import ApprovalBroker


@pytest.mark.asyncio
async def test_approval_resolves_true():
    broker = ApprovalBroker(asyncio.get_running_loop(), 2)
    task = asyncio.create_task(
        broker.request_approval("files", "read_file", {"path": "notes.txt"})
    )
    await asyncio.sleep(0)
    pending = broker.snapshot()
    assert len(pending) == 1
    assert broker.submit_decision(pending[0].request_id, True)
    assert await task is True


@pytest.mark.asyncio
async def test_timeout_fails_closed():
    broker = ApprovalBroker(asyncio.get_running_loop(), 0.01)
    assert await broker.request_approval("files", "read_file", {}) is False
    assert broker.snapshot() == []
