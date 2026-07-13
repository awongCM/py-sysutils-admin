import psutil
from pysysutils.models import BatteryStatusSnapshot


def format_secsleft(secsleft: int) -> str:
    if secsleft == psutil.POWER_TIME_UNLIMITED:
        return "charging"
    if secsleft == psutil.POWER_TIME_UNKNOWN:
        return "unknown"
    hours, rem = divmod(secsleft, 3600)
    minutes = rem // 60
    return f"{hours}h {minutes}m"


def collect_battery_status() -> BatteryStatusSnapshot:
    bat = psutil.sensors_battery()
    if bat is None:
        return BatteryStatusSnapshot(False, None, None, None, "n/a")
    return BatteryStatusSnapshot(
        present=True,
        percent=bat.percent,
        power_plugged=bat.power_plugged,
        secsleft=bat.secsleft if bat.secsleft not in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED) else None,
        secsleft_text=format_secsleft(bat.secsleft),
    )
