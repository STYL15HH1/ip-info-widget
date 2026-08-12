"""Small, UI-independent data models used by the application."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IPInfo:
    ip: str
    country: str
    country_code: str
    city: str = ""
    isp: str = ""


@dataclass(frozen=True)
class PingResult:
    reachable: bool
    latency_ms: int | None
    host: str


@dataclass(frozen=True)
class IPChange:
    changed_at: datetime
    old_ip: str
    new_ip: str
    country: str
    country_code: str

    def to_dict(self) -> dict[str, str]:
        return {
            "changed_at": self.changed_at.isoformat(timespec="seconds"),
            "old_ip": self.old_ip,
            "new_ip": self.new_ip,
            "country": self.country,
            "country_code": self.country_code,
        }


@dataclass(frozen=True)
class RefreshResult:
    info: IPInfo
    ping: PingResult | None
    change: IPChange | None
