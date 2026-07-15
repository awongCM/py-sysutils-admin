from __future__ import annotations

import sys
import time

from pysysutils.collectors.battery_health.base import NoopBackend
from pysysutils.models import BatteryHealthSnapshot

_CACHE_TTL_SECONDS = 60.0
_cache: tuple[float, BatteryHealthSnapshot] | None = None


def collect_battery_health(*, use_cache: bool = True) -> BatteryHealthSnapshot:
    global _cache
    if use_cache and _cache is not None:
        cached_at, snapshot = _cache
        if time.monotonic() - cached_at < _CACHE_TTL_SECONDS:
            return snapshot

    platform = sys.platform
    if platform.startswith("linux"):
        from pysysutils.collectors.battery_health.linux import LinuxBatteryHealthBackend

        snapshot = LinuxBatteryHealthBackend().collect()
    elif platform == "darwin":
        from pysysutils.collectors.battery_health.darwin import DarwinBatteryHealthBackend

        snapshot = DarwinBatteryHealthBackend().collect()
    elif platform == "win32":
        from pysysutils.collectors.battery_health.windows import WindowsBatteryHealthBackend

        snapshot = WindowsBatteryHealthBackend().collect()
    else:
        snapshot = NoopBackend().collect()

    if use_cache:
        _cache = (time.monotonic(), snapshot)
    return snapshot


def clear_battery_health_cache() -> None:
    global _cache
    _cache = None
