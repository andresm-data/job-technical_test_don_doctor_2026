"""Configuración del pipeline."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4


# =============================================================================
@dataclass(frozen=True, slots=True)
class SourceSpec:
    """Describe una fuente de datos de entrada.

    Attributes:
        name: Nombre corto de la fuente.
        table_name: Nombre de tabla para la capa raw.
        path: Ruta del archivo fuente.
        kind: Tipo de archivo.
        reader: Lector principal asignado.
        delimiter: Separador del archivo cuando aplica.
    """
    name: str
    table_name: str
    path: Path
    kind: Literal['csv', 'jsonl']
    reader: Literal['duckdb', 'pandas']
    delimiter: str = ','


# =============================================================================
@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Parámetros de ejecución del pipeline.

    Attributes:
        root_dir: Ruta raíz del proyecto.
        landing_dir: Carpeta con archivos fuente.
        warehouse_path: Ruta del archivo DuckDB.
        cutoff_at: Fecha de corte declarada para revisar estados cerrados.
        run_id: Identificador de la corrida.
    """
    root_dir: Path
    landing_dir: Path
    warehouse_path: Path
    cutoff_at: datetime
    run_id: str


# =============================================================================
def build_config(
    root_dir: Path,
    landing_dir: Path | None = None,
    warehouse_path: Path | None = None,
    cutoff_at: datetime | None = None
) -> PipelineConfig:
    """Construye la configuración del pipeline.

    Args:
        root_dir: Ruta raíz del proyecto.
        landing_dir: Carpeta con los archivos de entrada.
        warehouse_path: Ruta del archivo DuckDB.
        cutoff_at: Fecha usada para validar citas futuras con estado cerrado.

    Returns:
        PipelineConfig: Configuración lista para usar.
    """
    resolved_root = root_dir.resolve()

    resolved_landing = landing_dir or resolved_root / 'data' / 'landing'
    resolved_warehouse = warehouse_path or resolved_root / \
        'data' / 'warehouse' / 'don_doctor.db'

    resolved_cutoff = cutoff_at or datetime.fromisoformat(
        '2026-06-30T23:59:00'
    )

    resolved_run_id = str(uuid4())

    return PipelineConfig(
        root_dir=resolved_root,
        landing_dir=resolved_landing,
        warehouse_path=resolved_warehouse,
        cutoff_at=resolved_cutoff,
        run_id=resolved_run_id
    )


# =============================================================================
def build_sources(config: PipelineConfig) -> tuple[SourceSpec, ...]:
    """Devuelve la lista de fuentes a cargar.

    Args:
        config: Configuración general del pipeline.

    Returns:
        tuple[SourceSpec, ...]: Fuentes configuradas.
    """

    return (
        SourceSpec(
            name='ips_norte_citas',
            table_name='raw_citas_norte',
            path=config.landing_dir / 'ips_norte_citas.csv',
            kind='csv',
            reader='duckdb'
        ),
        SourceSpec(
            name='ips_sur_citas',
            table_name='raw_citas_sur',
            path=config.landing_dir / 'ips_sur_citas.csv',
            kind='csv',
            reader='duckdb'
        ),
        SourceSpec(
            name='ips_occidente_citas',
            table_name='raw_citas_occidente',
            path=config.landing_dir / 'ips_occidente_citas.csv',
            kind='csv',
            reader='duckdb',
            delimiter=';'
        ),
        SourceSpec(
            name='whatsapp_eventos',
            table_name='raw_whatsapp_eventos',
            path=config.landing_dir / 'whatsapp_eventos.jsonl',
            kind='jsonl',
            reader='pandas'
        ),
    )
