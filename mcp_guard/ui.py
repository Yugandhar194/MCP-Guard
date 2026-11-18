from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTextEdit, QVBoxLayout,
    QWidget,
)

from .approval import ApprovalBroker, ApprovalRequest


def pretty(value: Any) -> str:
    try:
        return json.dumps(value, indent=2, ensure_ascii=False, default=str)
    except Exception:
        return repr(value)


class ApprovalWindow(QMainWindow):
    def __init__(self, broker: ApprovalBroker) -> None:
        super().__init__()
        self.broker = broker
        self.setWindowTitle("MCP-Guard - Pending approvals")
        self.resize(900, 560)
        self.setMinimumSize(680, 420)

        central = QWidget()
        layout = QVBoxLayout(central)
        heading = QLabel("MCP-Guard")
        heading.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.status = QLabel("Protected MCP gateway - calls wait for your decision")
        layout.addWidget(heading)
        layout.addWidget(self.status)

        splitter = QSplitter()
        self.requests = QListWidget()
        self.requests.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        splitter.addWidget(self.requests)
        splitter.addWidget(self.details)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        actions = QHBoxLayout()
        self.allow_button = QPushButton("Allow once")
        self.block_button = QPushButton("Block")
        self.allow_button.clicked.connect(lambda: self.decide(True))
        self.block_button.clicked.connect(lambda: self.decide(False))
        actions.addStretch()
        actions.addWidget(self.block_button)
        actions.addWidget(self.allow_button)
        layout.addLayout(actions)
        self.setCentralWidget(central)

        self._items: dict[str, ApprovalRequest] = {}
        self.requests.currentItemChanged.connect(self.show_selected)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(300)
        self.refresh()

    def refresh(self) -> None:
        pending = self.broker.snapshot()
        selected = self.requests.currentItem()
        selected_id = selected.data(256) if selected else None
        self.requests.clear()
        self._items = {request.request_id: request for request in pending}
        for request in pending:
            item = QListWidgetItem(
                f"{request.server} / {request.tool}  [{request.request_id}]"
            )
            item.setData(256, request.request_id)
            self.requests.addItem(item)
            if request.request_id == selected_id:
                self.requests.setCurrentItem(item)
        if self.requests.count() and self.requests.currentRow() < 0:
            self.requests.setCurrentRow(0)
        if not pending:
            self.details.setPlainText("No pending requests. Waiting for MCP tool calls.")
            self.allow_button.setEnabled(False)
            self.block_button.setEnabled(False)
        self.status.setText(
            f"{len(pending)} request(s) awaiting decision - timeout: {self.broker.timeout_seconds}s"
        )
        self.show_selected()

    def selected_request(self) -> ApprovalRequest | None:
        item = self.requests.currentItem()
        return self._items.get(item.data(256)) if item else None

    def show_selected(self, *_args) -> None:
        request = self.selected_request()
        if request is None:
            return
        self.details.setPlainText(
            f"Request ID: {request.request_id}\n"
            f"Upstream server: {request.server}\n"
            f"Tool: {request.tool}\n\n"
            f"Arguments:\n{pretty(request.arguments)}"
        )
        self.allow_button.setEnabled(True)
        self.block_button.setEnabled(True)

    def decide(self, allowed: bool) -> None:
        request = self.selected_request()
        if request is not None:
            self.broker.submit_decision(request.request_id, allowed)
            self.refresh()

    def closeEvent(self, event) -> None:
        if self.broker.snapshot():
            answer = QMessageBox.question(
                self,
                "Pending approvals",
                "There are pending calls. Close the approval window anyway?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()
