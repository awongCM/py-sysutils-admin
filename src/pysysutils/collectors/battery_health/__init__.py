import sys

from pysysutils.collectors.battery_health.base import NoopBackend
from pysysutils.models import BatteryHealthSnapshot


def collect_battery_health() -> BatteryHealthSnapshot:
    platform = sys.platform
    if platform.startswith("linux"):
        from pysysutils.collectors.battery_health.linux import LinuxBatteryHealthBackend

        return LinuxBatteryHealthBackend().collect()
    if platform == "darwin":
        from pysysutils.collectors.battery_health.darwin import DarwinBatteryHealthBackend

        return DarwinBatteryHealthBackend().collect()
    if platform == "win32":
        from pysysutils.collectors.battery_health.windows import WindowsBatteryHealthBackend

        return WindowsBatteryHealthBackend().collect()
    return NoopBackend().collect()
