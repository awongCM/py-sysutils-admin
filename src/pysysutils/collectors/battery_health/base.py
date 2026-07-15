from abc import ABC, abstractmethod

from pysysutils.models import BatteryHealthSnapshot


class BatteryHealthBackend(ABC):
    @abstractmethod
    def collect(self) -> BatteryHealthSnapshot:
        ...


class NoopBackend(BatteryHealthBackend):
    def collect(self) -> BatteryHealthSnapshot:
        return BatteryHealthSnapshot(
            available=False,
            health_percent=None,
            cycle_count=None,
            design_capacity_mwh=None,
            full_charge_capacity_mwh=None,
            condition=None,
        )
