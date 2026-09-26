"""Transformaciones de las capas clean y mart."""
import duckdb

from .config import PipelineConfig


# =============================================================================
STATE_NORMALIZATION = {
    'ATD': 'ATENDIDA',
    'NAS': 'NO_ASISTIO',
    'CAN': 'CANCELADA',
    'REP': 'REAGENDADA',
    'PEN': 'PENDIENTE',
    'CONF': 'CONFIRMADA'
}


# =============================================================================
def build_clean_and_mart(
    connection: duckdb.DuckDBPyConnection,
    config: PipelineConfig,
) -> None:
    """Construye las capas clean y mart.

    Args:
        connection: Conexión abierta a DuckDB.
        config: Configuración de ejecución.
    """

    connection.execute(
        _build_stage_citas_sql(
            config.cutoff_at.isoformat(sep=" ")
        )
    )
    connection.execute(_build_audit_citas_sql())
    connection.execute(_build_clean_citas_sql())
    connection.execute(_build_stage_whatsapp_sql())
    connection.execute(_build_audit_whatsapp_sql())
    connection.execute(_build_clean_whatsapp_sql())
    connection.execute(_build_dim_ips_sql())
    connection.execute(_build_dim_paciente_sql())
    connection.execute(_build_dim_medico_sql())
    connection.execute(_build_dim_fecha_sql())
    connection.execute(_build_fact_citas_sql())
    connection.execute(_build_agg_ausentismo_sql())


# =============================================================================
def _build_stage_citas_sql(cutoff_at: str) -> str:
    """Genera el SQL de preparación de citas canónicas.

    Args:
        cutoff_at: Fecha de corte en texto.

    Returns:
        str: SQL de preparación.
    """
    return f"""
        CREATE OR REPLACE TABLE clean.stg_citas_canonicas AS
        WITH base AS (
            SELECT
                'NORTE' AS fuente,
                cita_id,
                paciente_id,
                CAST(edad AS INTEGER) AS edad,
                sexo,
                regimen,
                localidad,
                especialidad,
                medico_id,
                sede,
                canal_agendamiento,
                CAST(fecha_creacion AS TIMESTAMP) AS fecha_creacion,
                CAST(fecha_cita AS TIMESTAMP) AS fecha_cita,
                CAST(fecha_actualizacion AS TIMESTAMP) AS fecha_actualizacion,
                estado,
                CAST(recordatorio_enviado AS INTEGER) AS recordatorio_enviado,
                CAST(confirmada AS INTEGER) AS confirmada,
                CAST(gestion_recuperacion AS INTEGER) AS gestion_recuperacion,
                motivo_cierre,
                cita_origen_id,
                observaciones,
                NULL::VARCHAR AS documento_identidad,
                NULL::VARCHAR AS telefono,
                _run_id,
                _loaded_at
            FROM
                raw.raw_citas_norte

            UNION ALL

            SELECT
                'SUR' AS fuente,
                cita_id,
                paciente_id,
                CAST(edad AS INTEGER) AS edad,
                sexo,
                regimen,
                localidad,
                especialidad,
                medico_id,
                sede,
                canal_agendamiento,
                CAST(fecha_creacion AS TIMESTAMP) AS fecha_creacion,
                CAST(fecha_cita AS TIMESTAMP) AS fecha_cita,
                CAST(fecha_actualizacion AS TIMESTAMP) AS fecha_actualizacion,
                estado,
                CAST(recordatorio_enviado AS INTEGER) AS recordatorio_enviado,
                CAST(confirmada AS INTEGER) AS confirmada,
                CAST(gestion_recuperacion AS INTEGER) AS gestion_recuperacion,
                motivo_cierre,
                cita_origen_id,
                observaciones,
                documento_identidad,
                telefono,
                _run_id,
                _loaded_at
            FROM
                raw.raw_citas_sur

            UNION ALL

            SELECT
                'OCCIDENTE' AS fuente,
                id_cita AS cita_id,
                id_paciente AS paciente_id,
                CAST(edad_paciente AS INTEGER) AS edad,
                CASE genero
                    WHEN 'Femenino' THEN 'F'
                    WHEN 'Masculino' THEN 'M'
                    ELSE genero
                END AS sexo,
                regimen_salud AS regimen,
                localidad,
                especialidad,
                medico_id,
                sede,
                canal_agendamiento,
                CAST(fecha_creacion AS TIMESTAMP) AS fecha_creacion,
                CAST(fecha_hora_cita AS TIMESTAMP) AS fecha_cita,
                CAST(fecha_actualizacion AS TIMESTAMP) AS fecha_actualizacion,
                CASE estado_cita
                    WHEN 'ATD' THEN 'ATENDIDA'
                    WHEN 'NAS' THEN 'NO_ASISTIO'
                    WHEN 'CAN' THEN 'CANCELADA'
                    WHEN 'REP' THEN 'REAGENDADA'
                    WHEN 'PEN' THEN 'PENDIENTE'
                    WHEN 'CONF' THEN 'CONFIRMADA'
                    ELSE estado_cita
                END AS estado,
                CAST(recordatorio_enviado AS INTEGER) AS recordatorio_enviado,
                CAST(confirmada AS INTEGER) AS confirmada,
                CAST(gestion_recuperacion AS INTEGER) AS gestion_recuperacion,
                motivo_cierre,
                id_cita_origen AS cita_origen_id,
                observaciones,
                NULL::VARCHAR AS documento_identidad,
                NULL::VARCHAR AS telefono,
                _run_id,
                _loaded_at
            FROM
                raw.raw_citas_occidente
        ),
        ranked AS (
            SELECT
                fuente,
                cita_id,
                sha256(fuente || ':' || paciente_id) AS paciente_sk,
                edad,
                upper(sexo) AS sexo,
                regimen,
                localidad,
                especialidad,
                medico_id,
                sede,
                canal_agendamiento,
                fecha_creacion,
                fecha_cita,
                fecha_actualizacion,
                upper(estado) AS estado,
                recordatorio_enviado,
                confirmada,
                gestion_recuperacion,
                motivo_cierre,
                cita_origen_id,
                sha256(coalesce(documento_identidad, '')) AS documento_identidad_hash,
                sha256(coalesce(telefono, '')) AS telefono_hash,
                observaciones IS NOT NULL AND trim(observaciones) <> '' AS tiene_observaciones,
                COUNT(*) OVER (PARTITION BY fuente, cita_id) AS registros_fuente,
                ROW_NUMBER() OVER (
                    PARTITION BY fuente, cita_id
                    ORDER BY fecha_actualizacion DESC NULLS LAST, fecha_creacion DESC NULLS LAST, _loaded_at DESC
                ) AS version_rank,
                fecha_cita < fecha_creacion
                    OR fecha_actualizacion < fecha_creacion AS fecha_inconsistente,
                fecha_cita > TIMESTAMP '{cutoff_at}'
                    AND upper(estado) NOT IN ('PENDIENTE', 'CONFIRMADA') AS estado_cerrado_con_cita_futura,
                _run_id,
                _loaded_at
            FROM
                base
        )

        SELECT
            *,
            registros_fuente > 1 AS fue_duplicada_en_origen,
            NOT fecha_inconsistente AND NOT estado_cerrado_con_cita_futura AND version_rank = 1 AS pasa_reglas_base
        FROM
            ranked
    """


# =============================================================================
def _build_audit_citas_sql() -> str:
    """Genera el SQL para auditar citas rechazadas.

    Returns:
        str: SQL de auditoría.
    """
    return """
        CREATE OR REPLACE TABLE audit.audit_citas_rechazadas AS
        SELECT
            fuente,
            cita_id,
            CASE
                WHEN version_rank > 1 THEN 'version_antigua_duplicada'
                WHEN fecha_inconsistente THEN 'fecha_inconsistente'
                WHEN estado_cerrado_con_cita_futura THEN 'estado_cerrado_con_cita_futura'
                ELSE 'sin_regla'
            END AS razon_rechazo,
            fecha_creacion,
            fecha_cita,
            fecha_actualizacion,
            estado,
            registros_fuente,
            version_rank,
            _run_id,
            _loaded_at
        FROM
            clean.stg_citas_canonicas
        WHERE
            NOT pasa_reglas_base
    """


# =============================================================================
def _build_clean_citas_sql() -> str:
    """Genera el SQL final de citas limpias.

    Returns:
        str: SQL de la tabla clean.
    """
    return """
        CREATE OR REPLACE TABLE clean.clean_citas AS
        WITH whatsapp_validado AS (
            SELECT DISTINCT ref_cita
            FROM raw.raw_whatsapp_eventos
            WHERE ref_cita IS NOT NULL
        )
        SELECT
            fuente,
            cita_id,
            paciente_sk,
            edad,
            sexo,
            regimen,
            localidad,
            especialidad,
            medico_id,
            sede,
            canal_agendamiento,
            fecha_creacion,
            fecha_cita,
            fecha_actualizacion,
            estado,
            recordatorio_enviado AS recordatorio_fuente,
            CASE
                WHEN recordatorio_enviado = 1 AND w.ref_cita IS NOT NULL THEN 1
                ELSE 0
            END AS recordatorio_validado,
            confirmada,
            gestion_recuperacion,
            CASE
                WHEN estado = 'CANCELADA' AND fecha_actualizacion IS NOT NULL THEN date_diff('minute', fecha_actualizacion, fecha_cita)
                ELSE NULL
            END AS minutos_anticipacion_cancelacion,
            CASE
                WHEN estado IN ('ATENDIDA', 'NO_ASISTIO') THEN 1
                WHEN estado = 'CANCELADA' AND fecha_actualizacion IS NOT NULL
                    AND date_diff('minute', fecha_actualizacion, fecha_cita) < 120 THEN 1
                ELSE 0
            END AS ocupo_agenda,
            CASE
                WHEN estado = 'NO_ASISTIO' THEN 1
                WHEN estado = 'CANCELADA' AND fecha_actualizacion IS NOT NULL
                    AND date_diff('minute', fecha_actualizacion, fecha_cita) < 120 THEN 1
                ELSE 0
            END AS es_ausentismo,
            motivo_cierre,
            cita_origen_id,
            fue_duplicada_en_origen,
            fecha_inconsistente,
            estado_cerrado_con_cita_futura,
            documento_identidad_hash,
            telefono_hash,
            tiene_observaciones,
            _run_id,
            _loaded_at
        FROM
            clean.stg_citas_canonicas c
        LEFT JOIN whatsapp_validado w
            ON c.cita_id = w.ref_cita
        WHERE
            c.pasa_reglas_base
            AND c.version_rank = 1
    """


# =============================================================================
def _build_stage_whatsapp_sql() -> str:
    """Genera el SQL de preparación de eventos WhatsApp.

    Returns:
        str: SQL de preparación.
    """
    return """
        CREATE OR REPLACE TABLE clean.stg_whatsapp_eventos AS
        WITH citas_validas AS (
            SELECT cita_id FROM clean.clean_citas
        ),
        base AS (
            SELECT
                _id AS evento_id,
                to_timestamp(ts / 1000.0) AS fecha_evento,
                upper(tipo) AS tipo,
                upper(ips) AS fuente,
                ref_cita,
                destinatario,
                sha256(coalesce(destinatario, '')) AS destinatario_hash,
                plantilla,
                cuerpo,
                contexto_json,
                mensaje_json,
                payload_raw,
                _run_id,
                _loaded_at
            FROM
                raw.raw_whatsapp_eventos
        ), ranked AS (
            SELECT
                *,
                ref_cita IS NULL AS sin_ref_cita,
                ref_cita IS NOT NULL AND ref_cita NOT IN (SELECT cita_id FROM citas_validas) AS ref_cita_no_valida,
                ROW_NUMBER() OVER (
                    PARTITION BY tipo, fuente, coalesce(ref_cita, '__SIN_REF__'), coalesce(destinatario, '__SIN_DEST__'), fecha_evento
                    ORDER BY evento_id
                ) AS duplicate_rank,
                COUNT(*) OVER (
                    PARTITION BY tipo, fuente, coalesce(ref_cita, '__SIN_REF__'), coalesce(destinatario, '__SIN_DEST__'), fecha_evento
                ) AS duplicate_count
            FROM
                base
        )
        SELECT
            *,
            duplicate_count > 1 AS fue_duplicado_en_origen,
            NOT sin_ref_cita AND NOT ref_cita_no_valida AND duplicate_rank = 1 AS pasa_reglas_base
        FROM
            ranked
    """


# =============================================================================
def _build_audit_whatsapp_sql() -> str:
    """Genera el SQL de auditoría para eventos WhatsApp.

    Returns:
        str: SQL de auditoría.
    """

    return """
        CREATE OR REPLACE TABLE audit.audit_whatsapp_eventos_rechazados AS
        SELECT
            evento_id,
            fuente,
            ref_cita,
            tipo,
            fecha_evento,
            CASE
                WHEN sin_ref_cita THEN 'sin_ref_cita'
                WHEN ref_cita_no_valida THEN 'ref_cita_no_valida'
                WHEN duplicate_rank > 1 THEN 'evento_duplicado'
                ELSE 'sin_regla'
            END AS razon_rechazo,
            payload_raw,
            _run_id,
            _loaded_at
        FROM
            clean.stg_whatsapp_eventos
        WHERE
            NOT pasa_reglas_base
    """


# =============================================================================
def _build_clean_whatsapp_sql() -> str:
    """Genera el SQL final de WhatsApp limpio.

    Returns:
        str: SQL de la tabla clean.
    """

    return """
        CREATE OR REPLACE TABLE clean.clean_whatsapp_eventos AS
        SELECT
            evento_id,
            fecha_evento,
            tipo,
            fuente,
            ref_cita,
            destinatario_hash,
            plantilla,
            cuerpo,
            fue_duplicado_en_origen,
            _run_id,
            _loaded_at
        FROM
            clean.stg_whatsapp_eventos
        WHERE
            pasa_reglas_base
    """


# =============================================================================
def _build_dim_ips_sql() -> str:
    """Genera la dimensión de IPS.

    Returns:
        str: SQL de la dimensión.
    """

    return """
        CREATE OR REPLACE TABLE mart.dim_ips AS
        SELECT
            DISTINCT
                fuente AS ips_id,
                fuente AS ips_nombre
        FROM
            clean.clean_citas
    """


# =============================================================================
def _build_dim_paciente_sql() -> str:
    """Genera la dimensión de paciente seudonimizada.

    Returns:
        str: SQL de la dimensión.
    """
    return """
        CREATE OR REPLACE TABLE mart.dim_paciente AS
        WITH ranked AS (
            SELECT
                paciente_sk,
                edad,
                sexo,
                regimen,
                localidad,
                fuente,
                fecha_actualizacion,
                ROW_NUMBER() OVER (
                    PARTITION BY paciente_sk
                    ORDER BY fecha_actualizacion DESC NULLS LAST, fuente
                ) AS rn
            FROM
                clean.clean_citas
        )
        SELECT
            paciente_sk,
            edad AS edad_referencia,
            sexo,
            regimen,
            localidad,
            fuente AS ultima_fuente
        FROM
            ranked
        WHERE
            rn = 1
    """


# =============================================================================
def _build_dim_medico_sql() -> str:
    """Genera la dimensión de médico.

    Returns:
        str: SQL de la dimensión.
    """
    return """
        CREATE OR REPLACE TABLE mart.dim_medico AS
        SELECT
            DISTINCT
                medico_id,
                especialidad,
                sede,
                fuente AS ips_id
        FROM
            clean.clean_citas
    """


# =============================================================================
def _build_dim_fecha_sql() -> str:
    """Genera la dimensión de fecha.

    Returns:
        str: SQL de la dimensión.
    """
    return """
        CREATE OR REPLACE TABLE mart.dim_fecha AS
        WITH fechas AS (
            SELECT
                DISTINCT CAST(fecha_cita AS DATE) AS fecha_cita
            FROM
                clean.clean_citas
        )
        SELECT
            CAST(strftime(fecha_cita, '%Y%m%d') AS INTEGER) AS fecha_key,
            fecha_cita,
            CAST(strftime(fecha_cita, '%Y') AS INTEGER) AS anio,
            CAST(strftime(fecha_cita, '%m') AS INTEGER) AS mes,
            CAST(strftime(fecha_cita, '%d') AS INTEGER) AS dia,
            dayname(fecha_cita) AS dia_semana
        FROM
            fechas
    """


# =============================================================================
def _build_fact_citas_sql() -> str:
    """Genera la tabla de hechos de citas.

    Returns:
        str: SQL de hechos.
    """
    return """
        CREATE OR REPLACE TABLE mart.fact_citas AS
        SELECT
            c.cita_id,
            c.fuente AS ips_id,
            c.paciente_sk,
            c.medico_id,
            CAST(strftime(CAST(c.fecha_cita AS DATE), '%Y%m%d') AS INTEGER) AS fecha_key,
            c.fecha_creacion,
            c.fecha_cita,
            c.fecha_actualizacion,
            c.estado,
            c.recordatorio_fuente,
            c.recordatorio_validado,
            c.confirmada,
            c.gestion_recuperacion,
            c.minutos_anticipacion_cancelacion,
            c.ocupo_agenda,
            c.es_ausentismo,
            CASE WHEN c.estado = 'NO_ASISTIO' THEN 1 ELSE 0 END AS es_no_asistio,
            CASE WHEN c.estado = 'ATENDIDA' THEN 1 ELSE 0 END AS es_atendida,
            c.fue_duplicada_en_origen,
            c.tiene_observaciones
        FROM
            clean.clean_citas c
    """


# =============================================================================
def _build_agg_ausentismo_sql() -> str:
    """Genera el agregado mensual de ausentismo por IPS.

    Returns:
        str: SQL agregado.
    """
    return """
        CREATE OR REPLACE TABLE mart.agg_ausentismo_mensual_ips AS
        SELECT
            ips_id,
            date_trunc('month', fecha_cita) AS periodo_mes,
            SUM(ocupo_agenda) AS total_citas_base,
            SUM(es_atendida) AS citas_atendidas,
            SUM(es_no_asistio) AS citas_no_asistidas,
            CASE
                WHEN SUM(ocupo_agenda) = 0 THEN 0
                ELSE ROUND(SUM(es_ausentismo) * 100.0 / SUM(ocupo_agenda), 2)
            END AS tasa_ausentismo_pct
        FROM
            mart.fact_citas
        GROUP BY
            1, 2
    """
