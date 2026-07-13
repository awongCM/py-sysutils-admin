import psutil
from pysysutils.models import NetworkSnapshot


def collect_network() -> NetworkSnapshot:
    c = psutil.net_io_counters()
    return NetworkSnapshot(
        bytes_sent=c.bytes_sent,
        bytes_recv=c.bytes_recv,
        packets_sent=getattr(c, "packets_sent", None),
        packets_recv=getattr(c, "packets_recv", None),
        send_rate_bps=None,
        recv_rate_bps=None,
    )


def compute_rates(
    previous: NetworkSnapshot, current: NetworkSnapshot, elapsed: float
) -> tuple[float, float]:
    if elapsed <= 0:
        return 0.0, 0.0
    send = (current.bytes_sent - previous.bytes_sent) / elapsed
    recv = (current.bytes_recv - previous.bytes_recv) / elapsed
    return max(send, 0.0), max(recv, 0.0)
