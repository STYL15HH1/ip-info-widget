"""Public-IP lookup and Windows ping implementation."""

from __future__ import annotations

import json
import re
import subprocess
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.models import IPInfo, PingResult


class IPServiceError(RuntimeError):
    pass


class IPService:
    endpoint = "https://ipwho.is/"

    def fetch_public_ip(self) -> IPInfo:
        request = Request(
            f"{self.endpoint}?_={time.time_ns()}",
            headers={"User-Agent": "IPInfoWidget/2.0", "Cache-Control": "no-cache"},
        )
        try:
            with urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, ValueError, json.JSONDecodeError) as error:
            raise IPServiceError("Could not retrieve public IP information.") from error
        if not isinstance(payload, dict) or not payload.get("success", True):
            message = payload.get("message", "The IP service did not return data.") if isinstance(payload, dict) else "Invalid IP service response."
            raise IPServiceError(str(message))
        connection = payload.get("connection") if isinstance(payload.get("connection"), dict) else {}
        ip = str(payload.get("ip") or "")
        if not ip:
            raise IPServiceError("The IP service did not return an IP address.")
        return IPInfo(
            ip=ip,
            country=str(payload.get("country") or "Unknown location"),
            country_code=str(payload.get("country_code") or "").upper(),
            city=str(payload.get("city") or ""),
            isp=str(connection.get("isp") or ""),
        )

    @staticmethod
    def ping(host: str) -> PingResult:
        host = host.strip()
        if not host:
            return PingResult(False, None, "")
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "1500", host],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=3,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            match = re.search(r"(?:time|czas)\s*[=<]\s*(\d+)\s*ms", result.stdout + result.stderr, re.IGNORECASE)
            latency = int(match.group(1)) if match else (0 if result.returncode == 0 else None)
            return PingResult(result.returncode == 0, latency, host)
        except (OSError, subprocess.SubprocessError):
            return PingResult(False, None, host)
