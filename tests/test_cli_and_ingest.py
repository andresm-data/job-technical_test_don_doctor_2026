from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline import cli, ingest  # noqa


def test_build_parser_accepts_known_arguments() -> None:
    """Verifica que el parser entienda los argumentos de la CLI."""

    parser = cli.build_parser()
    args = parser.parse_args([
        "run",
        "--landing-dir",
        "/tmp/landing",
        "--warehouse-path",
        "/tmp/test.duckdb",
        "--cutoff-at",
        "2026-06-30T23:59:00",
    ])

    assert args.run == "run"
    assert args.landing_dir == Path("/tmp/landing")
    assert args.warehouse_path == Path("/tmp/test.duckdb")
    assert args.cutoff_at.isoformat() == "2026-06-30T23:59:00"


def test_main_executes_pipeline_with_expected_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica que main construya la configuración y ejecute el pipeline."""

    captured: dict[str, object] = {}

    def fake_run_pipeline(config) -> None:
        captured["config"] = config

    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pipeline.py",
            "run",
            "--landing-dir",
            "/tmp/landing",
            "--warehouse-path",
            "/tmp/test.duckdb",
            "--cutoff-at",
            "2026-07-01T00:00:00",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    config = captured["config"]
    assert config.root_dir == cli.PROJECT_ROOT.resolve()
    assert config.landing_dir == Path("/tmp/landing")
    assert config.warehouse_path == Path("/tmp/test.duckdb")
    assert config.cutoff_at.isoformat() == "2026-07-01T00:00:00"


def test_main_rejects_unknown_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica que la CLI rechace comandos distintos de run."""

    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "otro_comando"])

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2


def test_to_json_text_returns_none_for_non_dict() -> None:
    """Verifica la salida nula para valores que no son diccionarios."""

    assert ingest._to_json_text("texto") is None


def test_extract_value_returns_none_for_non_dict() -> None:
    """Verifica la salida nula cuando no hay diccionario."""

    assert ingest._extract_value(None, "ips") is None


def test_extract_value_returns_value_for_known_key() -> None:
    """Verifica la extracción parametrizada desde un diccionario."""

    payload = {"ips": "SUR", "ref_cita": "SUR-123"}

    assert ingest._extract_value(payload, "ips") == "SUR"
    assert ingest._extract_value(payload, "ref_cita") == "SUR-123"