"""Stateful refresh and change-detection service, independent of Tkinter."""

from __future__ import annotations

from datetime import datetime

from core.history import HistoryStore
from core.ip_service import IPService
from core.models import IPChange, RefreshResult


class IPMonitor:
    def __init__(self, service: IPService, history: HistoryStore) -> None:
        self.service = service
        self.history = history
        self.current_ip: str | None = None

    def refresh(self, ping_host: str, run_ping: bool) -> RefreshResult:
        info = self.service.fetch_public_ip()
        change = None
        if self.current_ip is not None and info.ip != self.current_ip:
            change = IPChange(
                changed_at=datetime.now().astimezone(),
                old_ip=self.current_ip,
                new_ip=info.ip,
                country=info.country,
                country_code=info.country_code,
            )
            self.history.add(change)
        self.current_ip = info.ip
        ping = self.service.ping(ping_host) if run_ping else None
        return RefreshResult(info=info, ping=ping, change=change)
