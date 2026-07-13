from typer.testing import CliRunner
from pysysutils.cli import app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "snapshot" in result.stdout


def test_cpu_json(mocker):
    from pysysutils.models import CpuSnapshot

    mocker.patch("pysysutils.cli.collect_cpu", return_value=CpuSnapshot(1.0, None, 1, 1))
    runner = CliRunner()
    result = runner.invoke(app, ["cpu", "--format", "json"])
    assert result.exit_code == 0
    assert "percent" in result.stdout


def test_watch_json_interrupts(mocker):
    mocker.patch("pysysutils.cli.build_snapshot", return_value=mocker.Mock(to_dict=lambda: {"ok": True}))
    mocker.patch("pysysutils.cli.time.sleep", side_effect=KeyboardInterrupt)
    runner = CliRunner()
    result = runner.invoke(app, ["watch", "--format", "json"])
    assert result.exit_code == 0
