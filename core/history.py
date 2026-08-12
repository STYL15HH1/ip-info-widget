"""Persistent, bounded public-IP change history."""

from __future__ import annotations

import json
from datetime import datetime

from core.models import IPChange
from core.storage import AppPaths


class HistoryStore:
    max_entries = 50

    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def load(self) -> list[dict[str, object]]:
        try:
            items = json.loads(self.paths.history_path.read_text(encoding="utf-8"))
            return items if isinstance(items, list) else []
        except (OSError, ValueError, json.JSONDecodeError):
            return []

    def add(self, change: IPChange) -> None:
        entries = self.load()
        entries.append(change.to_dict())
        self.save(entries)

    def save(self, entries: list[dict[str, object]]) -> None:
        self.paths.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.history_path.write_text(
            json.dumps(entries[-self.max_entries :], indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def clear(self) -> None:
        self.save([])

    @staticmethod
    def display_time(entry: dict[str, object]) -> str:
        try:
            return datetime.fromisoformat(str(entry["changed_at"])).strftime("%d.%m.%Y %H:%M:%S")
        except (KeyError, TypeError, ValueError):
            return str(entry.get("changed_at", ""))
