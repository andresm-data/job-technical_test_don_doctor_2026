"""Carga de datos a la capa raw."""
import json
from datetime import datetime

import duckdb
import pandas as pd

from .config import PipelineConfig, SourceSpec, build_sources
from .privacy import build_privacy_rules


# =============================================================================
def ingest_raw(config: PipelineConfig) -> None:
    """Carga las fuentes en la capa raw y registra reglas de privacidad.

    Args:
        config: Configuración de ejecución.
    """
    config.warehouse_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(config.warehouse_path)) as connection:
        _create_schemas(connection)

        for source in build_sources(config):
            if source.reader == 'duckdb':
                _load_csv_source(connection, source, config.run_id)
            else:
                _load_jsonl_source(connection, source, config.run_id)

        _persist_privacy_inventory(connection)


# =============================================================================
def _create_schemas(connection: duckdb.DuckDBPyConnection) -> None:
    """Crea los esquemas usados por el pipeline.

    Args:
        connection: Conexión abierta a DuckDB.
    """
    for schema_name in ('raw', 'clean', 'mart', 'audit', 'governance'):
        connection.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')


# =============================================================================
def _load_csv_source(
    connection: duckdb.DuckDBPyConnection,
    source: SourceSpec,
    run_id: str
) -> None:
    """Carga una fuente CSV usando DuckDB.

    Args:
        connection: Conexión abierta a DuckDB.
        source: Fuente a cargar.
        run_id: Identificador de la corrida.
    """
    delimiter_sql = f", delim = '{source.delimiter}'" if source.delimiter != "," else ""
    path_sql = str(source.path).replace("'", "''")

    source_name_sql = source.name.replace("'", "''")
    run_id_sql = run_id.replace("'", "''")

    query = f"""
        CREATE OR REPLACE TABLE raw.{source.table_name} AS
            SELECT
                *,
                '{source_name_sql}' AS _source_name,
                '{path_sql}' AS _source_file,
                '{run_id_sql}' AS _run_id,
                CURRENT_TIMESTAMP AS _loaded_at
            FROM
                read_csv_auto('{path_sql}', header = TRUE{delimiter_sql})
    """
    connection.execute(query)


# =============================================================================
def _load_jsonl_source(
    connection: duckdb.DuckDBPyConnection,
    source: SourceSpec,
    run_id: str
) -> None:
    """Carga una fuente JSONL usando Pandas.

    Args:
        connection: Conexión abierta a DuckDB.
        source: Fuente a cargar.
        run_id: Identificador de la corrida.
    """
    dataframe = pd.read_json(source.path, lines=True)

    raw_lines = source.path.read_text(encoding='utf-8').splitlines()
    dataframe = dataframe.copy()

    dataframe['mensaje_json'] = dataframe['mensaje'].map(_to_json_text)
    dataframe['contexto_json'] = dataframe['contexto'].map(_to_json_text)
    dataframe['payload_raw'] = raw_lines
    dataframe['destinatario'] = dataframe['mensaje'].map(
        lambda value: _extract_value(value, 'destinatario')
    )
    dataframe['ref_cita'] = dataframe['contexto'].map(
        lambda value: _extract_value(value, 'ref_cita')
    )
    dataframe['ips'] = dataframe['contexto'].map(
        lambda value: _extract_value(value, 'ips')
    )
    dataframe['plantilla'] = dataframe['mensaje'].map(
        lambda value: _extract_value(value, 'plantilla')
    )
    dataframe['cuerpo'] = dataframe['mensaje'].map(
        lambda value: _extract_value(value, 'cuerpo')
    )
    dataframe['_source_name'] = source.name
    dataframe['_source_file'] = str(source.path)
    dataframe['_run_id'] = run_id
    dataframe['_loaded_at'] = datetime.now()

    connection.register('raw_whatsapp_eventos_df', dataframe)
    connection.execute(
        """
        CREATE OR REPLACE TABLE raw.raw_whatsapp_eventos AS
            SELECT *
            FROM raw_whatsapp_eventos_df
        """
    )
    connection.unregister('raw_whatsapp_eventos_df')


# =============================================================================
def _persist_privacy_inventory(connection: duckdb.DuckDBPyConnection) -> None:
    """Guarda el inventario de privacidad dentro del warehouse.

    Args:
        connection: Conexión abierta a DuckDB.
    """
    rules = pd.DataFrame([rule.__dict__ for rule in build_privacy_rules()])
    connection.register('privacy_rules_df', rules)
    connection.execute(
        """
        CREATE OR REPLACE TABLE governance.data_privacy_inventory AS
            SELECT *
            FROM privacy_rules_df
        """
    )
    connection.unregister('privacy_rules_df')


# =============================================================================
def _to_json_text(value: object) -> str | None:
    """Convierte un valor a texto JSON si existe.

    Args:
        value: Valor a convertir.

    Returns:
        str | None: Texto JSON o nulo.
    """
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)

    return None


# =============================================================================
def _extract_value(value: object, key: str) -> str | None:
    """Extrae un valor específico desde un diccionario.

    Args:
        value: Diccionario original.
        key: Clave del valor a extraer.

    Returns:
        str | None: Valor asociado a la clave o nulo.
    """
    if isinstance(value, dict):
        return value.get(key)

    return None
