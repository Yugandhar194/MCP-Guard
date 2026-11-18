from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import threading
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .approval import ApprovalBroker
from .config import load_config
from .logging_setup import configure_logging
from .proxy import run_proxy
from .ui import ApprovalWindow


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP-Guard approval gateway")
    parser.add_argument("--config", default="config/servers.json")
    args = parser.parse_args()

    config = load_config(Path(args.config).expanduser().resolve())
    configure_logging()
    log = logging.getLogger("mcp_guard")
    loop = asyncio.new_event_loop()
    broker = ApprovalBroker(loop, config.approval_timeout_seconds)
    ready = threading.Event()
    errors: list[BaseException] = []

    def worker() -> None:
        asyncio.set_event_loop(loop)
        ready.set()
        try:
            loop.run_until_complete(run_proxy(config, broker))
        except BaseException as exc:
            errors.append(exc)
            log.exception("MCP proxy stopped")
        finally:
            tasks = asyncio.all_tasks(loop)
            for task in tasks:
                task.cancel()
            if tasks:
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.close()

    thread = threading.Thread(target=worker, name="mcp-proxy", daemon=True)
    thread.start()
    ready.wait()

    app = QApplication(sys.argv)
    window = ApprovalWindow(broker)
    window.show()
    exit_code = app.exec()

    if thread.is_alive():
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=3)
    return exit_code if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
