from types import SimpleNamespace
from pysysutils.collectors.network import collect_network, compute_rates


def test_collect_network(mocker):
    counters = SimpleNamespace(bytes_sent=1000, bytes_recv=2000, packets_sent=10, packets_recv=20)
    mocker.patch("pysysutils.collectors.network.psutil.net_io_counters", return_value=counters)
    snap = collect_network()
    assert snap.bytes_sent == 1000
    assert snap.bytes_recv == 2000


def test_compute_rates():
    prev = type("S", (), {"bytes_sent": 1000, "bytes_recv": 2000})()
    curr = type("S", (), {"bytes_sent": 2000, "bytes_recv": 4000})()
    send, recv = compute_rates(prev, curr, elapsed=1.0)
    assert send == 1000.0
    assert recv == 2000.0
