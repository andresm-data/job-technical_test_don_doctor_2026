WITH
    norte AS (
        SELECT
            'NORTE' AS fuente,
            cita_id,
            fecha_creacion,
            fecha_cita,
            fecha_actualizacion,
            estado
        FROM
            read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
    ),
    sur AS (
        SELECT
            'SUR' AS fuente,
            cita_id,
            fecha_creacion,
            fecha_cita,
            fecha_actualizacion,
            estado
        FROM
            read_csv_auto ('data/landing/ips_sur_citas.csv', header = true)
    ),
    occidente AS (
        SELECT
            'OCCIDENTE' AS fuente,
            id_cita AS cita_id,
            fecha_creacion,
            fecha_hora_cita AS fecha_cita,
            fecha_actualizacion,
            estado_cita AS estado
        FROM
            read_csv_auto (
                'data/landing/ips_occidente_citas.csv',
                header = true,
                delim = ';'
            )
    ),
    base AS (
        SELECT
            *
        FROM
            norte
        UNION ALL
        SELECT
            *
        FROM
            sur
        UNION ALL
        SELECT
            *
        FROM
            occidente
    )
SELECT
    fuente,
    cita_id,
    fecha_creacion,
    fecha_cita,
    fecha_actualizacion,
    estado,
    CASE
        WHEN CAST(fecha_cita AS TIMESTAMP) < CAST(fecha_creacion AS TIMESTAMP) THEN 'cita_antes_de_creacion'
        WHEN CAST(fecha_actualizacion AS TIMESTAMP) < CAST(fecha_creacion AS TIMESTAMP) THEN 'actualizacion_antes_de_creacion'
    END AS inconsistencia
FROM
    base
WHERE
    CAST(fecha_cita AS TIMESTAMP) < CAST(fecha_creacion AS TIMESTAMP)
    OR CAST(fecha_actualizacion AS TIMESTAMP) < CAST(fecha_creacion AS TIMESTAMP)
ORDER BY
    fuente,
    inconsistencia,
    fecha_creacion;