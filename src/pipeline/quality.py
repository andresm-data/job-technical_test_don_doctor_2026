"""Controles de calidad con Great Expectations."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import duckdb
import great_expectations as ge
import pandas as pd
from great_expectations.core.expectation_suite import ExpectationSuite

from .config import PipelineConfig


# =============================================================================
@dataclass(frozen=True, slots=True)
class QualityFinding:
    """Resume un resultado de validación.

    Attributes:
        suite_name: Nombre lógico del grupo de validación.
        expectation_name: Regla evaluada.
        success: Resultado de la regla.
        detail: Mensaje corto para entender el fallo.
    """
    suite_name: str
    expectation_name: str
    success: bool
    detail: str


# =============================================================================
class DataQualityError(RuntimeError):
    """Error levantado cuando falla una regla crítica."""
    pass


# =============================================================================
def run_quality_checks(connection: duckdb.DuckDBPyConnection, config: PipelineConfig) -> None:
    """Ejecuta validaciones sobre las tablas finales.

    Args:
        connection: Conexión abierta a DuckDB.
        config: Configuración de ejecución.

    Raises:
        DataQualityError: Si falla una regla crítica.
    """
    clean_citas = connection.sql("SELECT * FROM clean.clean_citas").df()
    clean_whatsapp = connection.sql(
        'SELECT * FROM clean.clean_whatsapp_eventos'
    ).df()
    fact_citas = connection.sql('SELECT * FROM mart.fact_citas').df()

    findings = []
    findings.extend(_validate_clean_citas(clean_citas, config.cutoff_at))
    findings.extend(_validate_clean_whatsapp(clean_whatsapp))
    findings.extend(_validate_fact_citas(fact_citas))

    _persist_findings(connection, findings)

    failures = [finding for finding in findings if not finding.success]

    if failures:
        messages = [
            f'{finding.suite_name}.{finding.expectation_name}: {finding.detail}'
            for finding in failures
        ]

        raise DataQualityError('; '.join(messages))


# =============================================================================
def _validate_clean_citas(dataframe: pd.DataFrame, cutoff_at: datetime) -> list[QualityFinding]:
    """Valida la tabla clean de citas.

    Args:
        dataframe: Datos a validar.
        cutoff_at: Fecha de corte configurada.

    Returns:
        list[QualityFinding]: Resultados resumidos.
    """
    dataset = dataframe.copy()
    dataset['estado_futuro_valido'] = (~(dataset['fecha_cita'] > pd.Timestamp(cutoff_at))) | (
        dataset['estado'].isin(['PENDIENTE', 'CONFIRMADA'])
    )
    batch = _build_batch(dataset, 'clean_citas_asset')
    expectations = [
        (
            'columns_match',
            ge.expectations.ExpectTableColumnsToMatchSet(
                column_set=[
                    'fuente',
                    'cita_id',
                    'paciente_sk',
                    'edad',
                    'sexo',
                    'regimen',
                    'localidad',
                    'especialidad',
                    'medico_id',
                    'sede',
                    'canal_agendamiento',
                    'fecha_creacion',
                    'fecha_cita',
                    'fecha_actualizacion',
                    'estado',
                    'recordatorio_fuente',
                    'recordatorio_validado',
                    'confirmada',
                    'gestion_recuperacion',
                    'motivo_cierre',
                    'cita_origen_id',
                    'fue_duplicada_en_origen',
                    'fecha_inconsistente',
                    'estado_cerrado_con_cita_futura',
                    'documento_identidad_hash',
                    'telefono_hash',
                    'tiene_observaciones',
                    '_run_id',
                    '_loaded_at',
                    'estado_futuro_valido'
                ]
            )
        ),
        (
            'cita_id_unique',
            ge.expectations.ExpectColumnValuesToBeUnique(column='cita_id')
        ),
        (
            'estado_valido',
            ge.expectations.ExpectColumnValuesToBeInSet(
                column='estado',
                value_set=[
                    'ATENDIDA', 'NO_ASISTIO', 'CANCELADA',
                    'REAGENDADA', 'PENDIENTE', 'CONFIRMADA'
                ]
            )
        ),
        (
            'sexo_valido',
            ge.expectations.ExpectColumnValuesToBeInSet(
                column='sexo', value_set=['F', 'M']
            )
        ),
        (
            'fecha_cita_mayor_o_igual_creacion',
            ge.expectations.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A='fecha_cita',
                column_B='fecha_creacion',
                or_equal=True
            )
        ),
        (
            'fecha_actualizacion_mayor_o_igual_creacion',
            ge.expectations.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A='fecha_actualizacion',
                column_B='fecha_creacion',
                or_equal=True
            )
        ),
        (
            'estado_futuro_valido',
            ge.expectations.ExpectColumnValuesToBeInSet(
                column='estado_futuro_valido', value_set=[True]
            )
        )
    ]
    results = [
        _run_expectation(batch, 'clean_citas', name, expectation)
        for name, expectation in expectations
    ]

    return results


# =============================================================================
def _validate_clean_whatsapp(dataframe: pd.DataFrame) -> list[QualityFinding]:
    """Valida la tabla clean de eventos WhatsApp.

    Args:
        dataframe: Datos a validar.

    Returns:
        list[QualityFinding]: Resultados resumidos.
    """
    batch = _build_batch(dataframe.copy(), 'clean_whatsapp_asset')

    expectations = [
        (
            'evento_id_unique',
            ge.expectations.ExpectColumnValuesToBeUnique(column='evento_id')
        ),
        (
            'ref_cita_not_null',
            ge.expectations.ExpectColumnValuesToNotBeNull(column='ref_cita')
        ),
        (
            'tipo_valido',
            ge.expectations.ExpectColumnValuesToBeInSet(
                column='tipo',
                value_set=['ENVIADO', 'ENTREGADO', 'LEIDO', 'RESPUESTA']
            )
        )
    ]
    return [
        _run_expectation(batch, 'clean_whatsapp', name, expectation)
        for name, expectation in expectations
    ]


# =============================================================================
def _validate_fact_citas(dataframe: pd.DataFrame) -> list[QualityFinding]:
    """Valida la tabla de hechos de citas.

    Args:
        dataframe: Datos a validar.

    Returns:
        list[QualityFinding]: Resultados resumidos.
    """
    dataset = dataframe.copy()
    dataset['entra_base_valida'] = dataset['entra_base_ausentismo'].isin(
        [0, 1]
    )
    batch = _build_batch(dataset, 'fact_citas_asset')

    expectations = [
        (
            'cita_id_unique',
            ge.expectations.ExpectColumnValuesToBeUnique(column='cita_id')
        ),
        (
            'ips_id_not_null',
            ge.expectations.ExpectColumnValuesToNotBeNull(column='ips_id')
        ),
        (
            'flags_base_validas',
            ge.expectations.ExpectColumnValuesToBeInSet(
                column='entra_base_valida', value_set=[True]
            )
        )
    ]

    return [
        _run_expectation(batch, 'fact_citas', name, expectation)
        for name, expectation in expectations
    ]


# =============================================================================
def _build_batch(dataframe: pd.DataFrame, asset_name: str) -> Any:
    """Crea un batch efímero de Great Expectations para un DataFrame.

    Args:
        dataframe: Datos a validar.
        asset_name: Nombre técnico del asset.

    Returns:
        Any: Lote listo para validar.
    """
    context = ge.get_context(mode='ephemeral')
    datasource = context.data_sources.add_pandas(name=f'{asset_name}_source')
    asset = datasource.add_dataframe_asset(name=asset_name)
    batch_definition = asset.add_batch_definition_whole_dataframe(
        'whole_dataframe'
    )

    return batch_definition.get_batch(
        batch_parameters={'dataframe': dataframe}
    )


# =============================================================================
def _run_expectation(
    batch: Any,
    suite_name: str,
    expectation_name: str,
    expectation: Any,
) -> QualityFinding:
    """Ejecuta una expectativa y la resume.

    Args:
        batch: Batch de Great Expectations.
        suite_name: Nombre del grupo de reglas.
        expectation_name: Nombre de la regla.
        expectation: Objeto expectativa.

    Returns:
        QualityFinding: Resumen del resultado.
    """
    suite = ExpectationSuite(
        name=f'{suite_name}_{expectation_name}', expectations=[expectation]
    )
    result = batch.validate(suite)

    return _to_finding(suite_name, expectation_name, result.to_json_dict())


# =============================================================================
def _persist_findings(
    connection: duckdb.DuckDBPyConnection,
    findings: list[QualityFinding],
) -> None:
    """Guarda el resultado de calidad dentro del warehouse.

    Args:
        connection: Conexión abierta a DuckDB.
        findings: Hallazgos resumidos.
    """
    dataframe = pd.DataFrame([finding.__dict__ for finding in findings])
    connection.register('quality_findings_df', dataframe)
    connection.execute(
        """
        CREATE OR REPLACE TABLE governance.quality_findings AS
            SELECT *
            FROM quality_findings_df
        """
    )
    connection.unregister('quality_findings_df')


# =============================================================================
def _to_finding(
    suite_name: str,
    expectation_name: str,
    result: dict,
) -> QualityFinding:
    """Convierte un resultado de Great Expectations a un resumen corto.

    Args:
        suite_name: Nombre del grupo de validación.
        expectation_name: Nombre de la regla.
        result: Respuesta original de Great Expectations.

    Returns:
        QualityFinding: Resumen del resultado.
    """
    detail = 'ok'

    if not result.get('success', False):
        unexpected = result.get('result', {}).get('unexpected_count')
        detail = f'unexpected_count={unexpected}'

    return QualityFinding(
        suite_name=suite_name,
        expectation_name=expectation_name,
        success=bool(result.get('success', False)),
        detail=detail
    )
