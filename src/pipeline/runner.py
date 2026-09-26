"""Orquestación del pipeline."""
import duckdb

from .config import PipelineConfig
from .ingest import ingest_raw
from .quality import run_quality_checks
from .transform import build_clean_and_mart


# =============================================================================
def run_pipeline(config: PipelineConfig) -> None:
    """Ejecuta el pipeline completo.

    Args:
        config: Configuración de ejecución.
    """
    ingest_raw(config)

    with duckdb.connect(str(config.warehouse_path)) as connection:
        build_clean_and_mart(connection, config)
        run_quality_checks(connection, config)
