from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import duckdb
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.runner import run_pipeline  # noqa
from pipeline.quality import DataQualityError, run_quality_checks  # noqa
from pipeline.config import build_config, build_sources  # noqa


@pytest.fixture()
def warehouse_path(tmp_path: Path) -> Path:
    """Devuelve una ruta temporal para el warehouse."""
    return tmp_path / "test_pipeline.duckdb"


def test_build_sources_uses_expected_readers() -> None:
    """Verifica la configuración esperada de las fuentes."""

    config = build_config(root_dir=PROJECT_ROOT)
    sources = {source.name: source for source in build_sources(config)}

    assert sources["ips_norte_citas"].reader == "duckdb"
    assert sources["ips_sur_citas"].reader == "duckdb"
    assert sources["ips_occidente_citas"].delimiter == ";"
    assert sources["whatsapp_eventos"].reader == "pandas"


def test_build_config_generates_uuid_run_id() -> None:
    """Verifica que cada configuración use un UUID aleatorio."""

    first_config = build_config(root_dir=PROJECT_ROOT)
    second_config = build_config(root_dir=PROJECT_ROOT)

    assert UUID(first_config.run_id)
    assert UUID(second_config.run_id)
    assert first_config.run_id != second_config.run_id


def test_pipeline_runs_twice_without_duplicates(warehouse_path: Path) -> None:
    """Verifica que el pipeline no duplique datos al correr dos veces."""

    first_config = build_config(
        root_dir=PROJECT_ROOT, warehouse_path=warehouse_path)
    second_config = build_config(
        root_dir=PROJECT_ROOT, warehouse_path=warehouse_path)

    run_pipeline(first_config)
    first_counts = _collect_counts(warehouse_path)

    run_pipeline(second_config)
    second_counts = _collect_counts(warehouse_path)

    assert first_counts == second_counts
    assert second_counts["raw_norte"] > 0
    assert second_counts["clean_citas"] == second_counts["fact_citas"]


def test_clean_and_fact_reuse_ausentismo_flags(warehouse_path: Path) -> None:
    """Verifica que clean calcule la regla y fact la reutilice."""

    config = build_config(root_dir=PROJECT_ROOT, warehouse_path=warehouse_path)
    run_pipeline(config)

    with duckdb.connect(str(warehouse_path)) as connection:
        clean_columns = {
            row[0] for row in connection.sql("DESCRIBE clean.clean_citas").fetchall()
        }
        fact_columns = {
            row[0] for row in connection.sql("DESCRIBE mart.fact_citas").fetchall()
        }

        assert "minutos_anticipacion_cancelacion" in clean_columns
        assert "ocupo_agenda" in clean_columns
        assert "es_ausentismo" in clean_columns
        assert "minutos_anticipacion_cancelacion" in fact_columns
        assert "ocupo_agenda" in fact_columns
        assert "es_ausentismo" in fact_columns

        mismatch_count = connection.sql(
            """
            SELECT COUNT(*)
            FROM mart.fact_citas f
            JOIN clean.clean_citas c USING (cita_id)
            WHERE f.ocupo_agenda <> c.ocupo_agenda
               OR f.es_ausentismo <> c.es_ausentismo
               OR coalesce(f.minutos_anticipacion_cancelacion, -999999)
                  <> coalesce(c.minutos_anticipacion_cancelacion, -999999)
            """
        ).fetchone()[0]
        invalid_count = connection.sql(
            """
            SELECT COUNT(*)
            FROM clean.clean_citas
            WHERE es_ausentismo > ocupo_agenda
            """
        ).fetchone()[0]

        assert mismatch_count == 0
        assert invalid_count == 0


def test_agg_ausentismo_uses_clean_definition(warehouse_path: Path) -> None:
    """Verifica que el agregado use la definición calculada en clean."""

    config = build_config(root_dir=PROJECT_ROOT, warehouse_path=warehouse_path)
    run_pipeline(config)

    with duckdb.connect(str(warehouse_path)) as connection:
        mismatch_count = connection.sql(
            """
            WITH esperado AS (
                SELECT
                    ips_id,
                    date_trunc('month', fecha_cita) AS periodo_mes,
                    SUM(ocupo_agenda) AS total_citas_base,
                    ROUND(
                        CASE
                            WHEN SUM(ocupo_agenda) = 0 THEN 0
                            ELSE SUM(es_ausentismo) * 100.0 / SUM(ocupo_agenda)
                        END,
                        2
                    ) AS tasa_esperada
                FROM mart.fact_citas
                GROUP BY 1, 2
            )
            SELECT COUNT(*)
            FROM mart.agg_ausentismo_mensual_ips a
            JOIN esperado e
                ON a.ips_id = e.ips_id
               AND a.periodo_mes = e.periodo_mes
            WHERE a.total_citas_base <> e.total_citas_base
               OR a.tasa_ausentismo_pct <> e.tasa_esperada
            """
        ).fetchone()[0]

        assert mismatch_count == 0


def test_quality_fails_when_estado_goes_outside_catalog(warehouse_path: Path) -> None:
    """Verifica que calidad falle cuando el estado sale del catálogo."""

    config = build_config(root_dir=PROJECT_ROOT, warehouse_path=warehouse_path)
    run_pipeline(config)

    with duckdb.connect(str(warehouse_path)) as connection:
        connection.execute(
            """
            UPDATE clean.clean_citas
            SET estado = 'FUERA_DE_CATALOGO'
            WHERE cita_id = (SELECT cita_id FROM clean.clean_citas LIMIT 1)
            """
        )
        with pytest.raises(DataQualityError):
            run_quality_checks(connection, config)


def _collect_counts(warehouse_path: Path) -> dict[str, int]:
    """Devuelve conteos básicos del warehouse.

    Args:
        warehouse_path: Ruta de la base a revisar.

    Returns:
        dict[str, int]: Conteos de tablas clave.
    """

    with duckdb.connect(str(warehouse_path)) as connection:
        return {
            "raw_norte": connection.sql("SELECT COUNT(*) FROM raw.raw_citas_norte").fetchone()[0],
            "raw_sur": connection.sql("SELECT COUNT(*) FROM raw.raw_citas_sur").fetchone()[0],
            "raw_occidente": connection.sql("SELECT COUNT(*) FROM raw.raw_citas_occidente").fetchone()[0],
            "raw_whatsapp": connection.sql("SELECT COUNT(*) FROM raw.raw_whatsapp_eventos").fetchone()[0],
            "clean_citas": connection.sql("SELECT COUNT(*) FROM clean.clean_citas").fetchone()[0],
            "clean_whatsapp": connection.sql("SELECT COUNT(*) FROM clean.clean_whatsapp_eventos").fetchone()[0],
            "fact_citas": connection.sql("SELECT COUNT(*) FROM mart.fact_citas").fetchone()[0],
        }
