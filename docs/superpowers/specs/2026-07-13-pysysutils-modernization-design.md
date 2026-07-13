# PySysUtils Modernization — Design Spec

**Date:** 2026-07-13  
**Status:** Approved for implementation  
**Scope:** Option C — interactive CLI for humans **and** scriptable health checks for automation

---

## 1. Summary

Modernize the legacy single-file `py-sysutils-admin.py` into **pysysutils**, a cross-platform Python 3.10+ package that monitors machine health on Windows, macOS, and Linux.

The tool provides:

- **Human-facing CLI** — snapshot reports, live watch mode, resource-specific commands
- **Machine-facing automation** — JSON output, configurable thresholds, exit codes for cron/CI
- **Battery monitoring** — live status (all platforms via psutil) and degradation health (platform-specific backends)

The existing script remains in the repo during migration but is superseded by the new package. It may be removed in a follow-up PR after the new CLI reaches feature parity.

---

## 2. Goals

| Goal | Success criteria |
|------|------------------|
| Cross-platform parity | Same commands and JSON schema on Windows, macOS, Linux |
| Interactive monitoring | `snapshot`, `watch`, and per-resource commands with readable output |
| Automation | `check` command with exit codes; `--format json` on all commands |
| Battery coverage | Status everywhere; health metrics when OS exposes them |
| Reliability | Unit tests with mocked psutil; CI matrix on three OS targets |
| Installability | `pip install -e .` and console script `pysysutils` |

---

## 3. Non-Goals (v1)

- Web dashboard or remote multi-host monitoring
- Historical time-series database or alerting integrations (Slack, email)
- PyPI publication (optional Phase 4 stretch)
- GPU or temperature sensors (future collectors)
- Replacing dedicated tools (htop, btop) — this is a lightweight health utility

---

## 4. Architecture

### 4.1 High-level flow

```
User / Script
     │
     ▼
  CLI (Typer)
     │
     ├── snapshot / watch / <resource>
     │        │
     │        ▼
     │   Collectors ──► psutil (+ platform backends for battery health)
     │        │
     │        ▼
     │   HealthEvaluator (thresholds → status)
     │        │
     │        ▼
     │   Formatters (table │ json)
     │
     └── check ──► HealthEvaluator ──► exit code (0/1/2)
```

### 4.2 Design principles

1. **Collectors return data, never print.** All I/O lives in CLI or formatters.
2. **Structured models everywhere.** Dataclasses (stdlib) for snapshots; no ad-hoc dicts in business logic.
3. **Graceful degradation.** Missing battery, inaccessible process, or unavailable health field → `None` / skipped, not crash.
4. **Platform logic isolated.** Battery health backends live in OS-specific modules behind a common interface.
5. **Testability.** Collectors accept optional psutil-like injection for unit tests.

### 4.3 Package layout

```
pyproject.toml
README.md
src/pysysutils/
├── __init__.py              # __version__
├── __main__.py              # python -m pysysutils
├── cli.py                     # Typer app + command registration
├── models.py                  # dataclasses for all snapshots
├── health.py                  # threshold evaluation + aggregate status
├── config.py                  # load thresholds from defaults + TOML (Phase 3)
├── collectors/
│   ├── __init__.py
│   ├── base.py                # Collector protocol / helpers
│   ├── cpu.py
│   ├── memory.py
│   ├── processes.py
│   ├── disk.py
│   ├── network.py
│   ├── battery_status.py
│   └── battery_health/
│       ├── __init__.py        # factory: pick platform backend
│       ├── base.py            # BatteryHealthBackend ABC
│       ├── linux.py
│       ├── darwin.py
│       └── windows.py
└── formatters/
    ├── __init__.py
    ├── table.py               # Rich tables for human output
    └── json_fmt.py            # JSON serialization

tests/
├── conftest.py                # fixtures, mock psutil helpers
├── test_models.py
├── test_cpu.py
├── test_memory.py
├── test_processes.py
├── test_disk.py
├── test_network.py
├── test_battery_status.py
├── test_battery_health.py
├── test_health.py
├── test_formatters.py
└── test_cli.py
```

---

## 5. Data Models

All models live in `src/pysysutils/models.py`. Each exposes a `to_dict()` method for JSON formatting.

### 5.1 Health status enum

```python
class HealthLevel(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    SKIPPED = "skipped"   # e.g. no battery on desktop
```

### 5.2 Resource snapshots

**CpuSnapshot**
- `percent: float` — overall CPU usage (0–100)
- `per_cpu: list[float] | None` — per-core percentages when available
- `count_logical: int`
- `count_physical: int | None`

**MemorySnapshot**
- `total: int` — bytes
- `available: int`
- `used: int`
- `free: int`
- `percent: float`
- `swap_total: int | None`
- `swap_used: int | None`
- `swap_percent: float | None`

**ProcessInfo**
- `pid: int`
- `name: str`
- `username: str | None`
- `cpu_percent: float | None`
- `memory_percent: float`
- `status: str | None`

**ProcessSnapshot**
- `processes: list[ProcessInfo]` — sorted by memory_percent desc by default

**DiskPartition**
- `device: str`
- `mountpoint: str`
- `fstype: str`
- `total: int`
- `used: int`
- `free: int`
- `percent: float`

**DiskSnapshot**
- `partitions: list[DiskPartition]`

**NetworkSnapshot**
- `bytes_sent: int`
- `bytes_recv: int`
- `packets_sent: int | None`
- `packets_recv: int | None`
- `send_rate_bps: float | None` — populated in watch / repeated sampling
- `recv_rate_bps: float | None`

**BatteryStatusSnapshot**
- `present: bool`
- `percent: float | None`
- `power_plugged: bool | None`
- `secsleft: int | None` — `None` when unknown/unlimited
- `secsleft_text: str` — human label: `"2h 14m"`, `"charging"`, `"unknown"`

**BatteryHealthSnapshot**
- `available: bool` — whether health data was retrieved
- `health_percent: float | None` — current max / design capacity × 100
- `cycle_count: int | None`
- `design_capacity_mwh: int | None`
- `full_charge_capacity_mwh: int | None`
- `condition: str | None` — e.g. `"Normal"`, `"Service Recommended"`

**BatterySnapshot** (composite)
- `status: BatteryStatusSnapshot`
- `health: BatteryHealthSnapshot`

**SystemSnapshot** (aggregate for `snapshot` command)
- `timestamp: datetime`
- `platform: str` — `sys.platform`
- `hostname: str`
- `cpu: CpuSnapshot`
- `memory: MemorySnapshot`
- `disk: DiskSnapshot`
- `network: NetworkSnapshot`
- `battery: BatterySnapshot`
- `top_processes: ProcessSnapshot`
- `overall: HealthLevel`
- `issues: list[str]` — human-readable problem descriptions

---

## 6. Collectors

Each collector is a function or small class with signature:

```python
def collect_*() -> *Snapshot: ...
```

Collectors use `psutil` directly. Process iteration catches `psutil.NoSuchProcess`, `psutil.AccessDenied`, and `psutil.ZombieProcess` per process — never bare `except`.

### 6.1 CPU (`collectors/cpu.py`)

- `psutil.cpu_percent(interval=0.1)` for snapshot (short interval acceptable)
- `psutil.cpu_count(logical=True/False)` for core counts
- Optional `psutil.cpu_percent(percpu=True)` for per-core data

### 6.2 Memory (`collectors/memory.py`)

- `psutil.virtual_memory()` for RAM
- `psutil.swap_memory()` for swap; handle platforms without swap gracefully

### 6.3 Processes (`collectors/processes.py`)

- `psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status'])`
- Fix legacy bug: use **`pid`**, not `ppid`
- Default sort: `memory_percent` descending
- `top` parameter limits result count (default 10 for snapshot, configurable via CLI)

### 6.4 Disk (`collectors/disk.py`)

- **Do not use `os.statvfs`** — not cross-platform
- `psutil.disk_partitions(all=False)` then `psutil.disk_usage(mountpoint)` per partition
- Skip partitions that raise `PermissionError` or `OSError`

### 6.5 Network (`collectors/network.py`)

- `psutil.net_io_counters()` for cumulative counters
- Rate calculation: caller passes previous sample + elapsed time, or collector exposes `sample_network_rate(interval=1.0)` for watch mode

### 6.6 Battery status (`collectors/battery_status.py`)

- `psutil.sensors_battery()` → if `None`, return `BatteryStatusSnapshot(present=False, ...)`
- Map `secsleft` special values (`POWER_TIME_UNLIMITED`, `POWER_TIME_UNKNOWN`) to readable `secsleft_text`

### 6.7 Battery health (`collectors/battery_health/`)

**Factory** (`__init__.py`):

```python
def collect_battery_health() -> BatteryHealthSnapshot:
    backend = _get_backend()  # linux | darwin | windows | noop
    return backend.collect()
```

| Platform | Backend | Data source |
|----------|---------|-------------|
| Linux | `linux.py` | `/sys/class/power_supply/BAT*/energy_full_design`, `energy_full`, `cycle_count` (when present) |
| macOS | `darwin.py` | `ioreg -r -c AppleSmartBattery` parsed output |
| Windows | `windows.py` | `win32api` optional dep **or** subprocess `powercfg /batteryreport` parse (no extra dep for v1) |
| Other / no data | `base.NoopBackend` | `available=False` |

Health percent formula when capacities known:

```
health_percent = (full_charge_capacity / design_capacity) * 100
```

All subprocess calls: timeout 5s, catch failures, return `available=False`.

---

## 7. Health Evaluation

Module: `src/pysysutils/health.py`

### 7.1 Threshold configuration

Defaults (overridable via CLI flags and later TOML config):

| Check | Default warning | Default critical |
|-------|-----------------|------------------|
| CPU percent | ≥ 85 | ≥ 95 |
| Memory percent | ≥ 85 | ≥ 95 |
| Disk percent (any mount) | ≥ 85 | ≥ 95 |
| Swap percent | ≥ 70 | ≥ 90 |
| Battery charge (discharging) | ≤ 20 | ≤ 10 |
| Battery health percent | ≤ 80 | ≤ 60 |

### 7.2 Evaluation rules

- Evaluate each enabled check independently → `HealthLevel`
- **Overall status** = max severity across checks (critical > warning > healthy)
- Checks with `SKIPPED` (no battery) do not affect overall status
- Return `issues: list[str]` e.g. `"Memory usage at 91% (critical threshold: 95%)"`

### 7.3 Exit codes (`check` command)

| Code | Meaning |
|------|---------|
| 0 | All checks healthy |
| 1 | One or more warnings, no critical |
| 2 | One or more critical |

---

## 8. CLI Design

Framework: **Typer** (commands, `--help`, type validation)  
Output: **Rich** (tables, colors, live refresh)

Console script entry point: `pysysutils = pysysutils.cli:app`

### 8.1 Global options

```
--format [table|json]   default: table
--no-color              disable Rich styling
-v, --verbose           debug logging
```

### 8.2 Commands

#### `pysysutils snapshot`

One-shot full system report. Default format: Rich table sections for CPU, Memory, Disk, Network, Battery, Top Processes, Overall Status.

```
pysysutils snapshot
pysysutils snapshot --format json
pysysutils snapshot --top 20
```

#### `pysysutils watch`

Live refreshing dashboard. Default refresh interval: 2 seconds. Ctrl+C exits cleanly (exit code 0).

```
pysysutils watch
pysysutils watch --interval 1
pysysutils watch --format json   # prints JSON lines each tick
```

#### `pysysutils cpu | memory | disk | network | processes | battery`

Resource-specific commands. Each supports `--format json`.

```
pysysutils processes --top 15 --sort memory
pysysutils battery --health
pysysutils network --watch         # live rate display
```

#### `pysysutils check`

Automation-oriented health gate. Always respects thresholds. JSON output optional.

```
pysysutils check
pysysutils check --cpu-max 90 --mem-max 85 --disk-max 90
pysysutils check --battery-min 20 --battery-health-min 70
pysysutils check --format json
```

Prints summary to stderr (table) or stdout (json). Exit code per section 7.3.

### 8.3 Human output examples

**Snapshot (table)** — sectioned Rich panels with color-coded health:
- Green: healthy metrics
- Yellow: warning range
- Red: critical range

**Watch** — single Rich `Live` display updating CPU, memory, disk bar, network rates, battery row.

### 8.4 JSON schema stability

JSON keys use `snake_case` matching `to_dict()` output. Field presence is stable; nullable fields explicit as `null`. Version field:

```json
{ "schema_version": "1.0", ... }
```

---

## 9. Cross-Platform Considerations

| Concern | Approach |
|---------|----------|
| Disk paths | Use `psutil.disk_partitions()` — no hardcoded `/` |
| Windows battery health | Subprocess `powercfg /batteryreport /output ...` + HTML parse |
| macOS battery health | Subprocess `ioreg` parse |
| Linux battery health | Read sysfs; handle multiple `BAT*` entries |
| Process access denied | Skip process, continue iteration |
| No battery (desktop/VM) | `present=False`, health `available=False`, checks skipped |
| Console encoding | Rich handles Unicode; JSON uses UTF-8 |

---

## 10. Dependencies

**Runtime (pyproject.toml):**
- `psutil>=5.9.0`
- `typer>=0.12.0`
- `rich>=13.0.0`

**Dev:**
- `pytest>=8.0`
- `pytest-mock>=3.0`

**Optional (not v1):** `pywin32` for native Windows WMI — deferred; use `powercfg` subprocess instead.

**Python:** `>=3.10`

---

## 11. Testing Strategy

### 11.1 Unit tests

- Mock `psutil` return values via `pytest-mock` / custom fakes in `conftest.py`
- Each collector: happy path, empty/missing data, permission errors
- Battery health backends: fixture files simulating sysfs/ioreg/powercfg output
- Health evaluator: threshold boundary tests (84 vs 85, etc.)
- Formatters: snapshot JSON round-trip key presence
- CLI: `typer.testing.CliRunner` for `--help`, `--format json`, exit codes on `check`

### 11.2 CI (GitHub Actions)

Matrix: `ubuntu-latest`, `macos-latest`, `windows-latest` × Python 3.10, 3.12

Steps: checkout → install `[dev]` extras → `pytest -v`

Integration smoke (optional job): run `pysysutils snapshot --format json` on each OS (no assertions on values, only valid JSON + exit 0).

---

## 12. Migration from Legacy Script

1. New package developed alongside `py-sysutils-admin.py`
2. README updated to document `pysysutils` as primary interface
3. Legacy script marked deprecated in README with pointer to new CLI
4. Follow-up PR may remove legacy script after v1 release

Command mapping:

| Legacy | New |
|--------|-----|
| `c` (cpu/mem processes) | `pysysutils processes` or `pysysutils snapshot` |
| `n` (network) | `pysysutils network --watch` |
| `d` (disk) | `pysysutils disk` |

---

## 13. Implementation Phases

| Phase | Deliverable |
|-------|-------------|
| **1 — Foundation** | Package scaffold, models, CPU/memory/disk/process collectors, tests, CI |
| **2 — CLI** | `snapshot`, resource commands, Rich formatters, JSON output |
| **3 — Health + automation** | Battery status + health backends, `health.py`, `check` command, exit codes |
| **4 — Live + polish** | `watch` mode, network rates, README, config file support (optional) |

Phases are sequential; each produces working, testable software.

---

## 14. Error Handling

- Collector failures → log warning (if verbose), include partial snapshot with error note in `issues`
- CLI invalid flags → Typer error message, exit code 2 for usage errors (distinct from health critical)
- Watch mode Ctrl+C → clean shutdown message, exit 0
- Subprocess timeouts (battery health) → `available=False`, no stack trace to user

---

## 15. Open Questions (resolved)

| Question | Decision |
|----------|----------|
| Primary use case | **Option C** — CLI + automation equally |
| Battery scope | Status + health (platform-dependent health) |
| Config file | Phase 3+ optional TOML; CLI flags sufficient for v1 |
| Framework | Typer + Rich |
| Data models | stdlib dataclasses |

---

## 16. Acceptance Criteria (v1 complete)

- [ ] `pip install -e ".[dev]"` succeeds on all three OS targets
- [ ] `pysysutils snapshot` prints readable report; `--format json` valid JSON
- [ ] `pysysutils watch` refreshes live until Ctrl+C
- [ ] `pysysutils check` returns exit codes 0/1/2 per thresholds
- [ ] `pysysutils battery --health` shows status; health when OS provides data
- [ ] All unit tests pass in CI matrix
- [ ] No use of `os.statvfs` or bare `except`
- [ ] README documents all commands with examples
