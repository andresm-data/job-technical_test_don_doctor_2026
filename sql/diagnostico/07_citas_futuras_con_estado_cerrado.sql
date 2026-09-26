WITH
    norte AS (
        SELECT
            'NORTE' AS fuente,
            cita_id,
            fecha_cita,
            estado
        FROM
            read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
    ),
    sur AS (
        SELECT
            'SUR' AS fuente,
            cita_id,
            fecha_cita,
            estado
        FROM
            read_csv_auto ('data/landing/ips_sur_citas.csv', header = true)
    ),
    occidente AS (
        SELECT
            'OCCIDENTE' AS fuente,
            id_cita AS cita_id,
            fecha_hora_cita AS fecha_cita,
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
    fecha_cita,
    estado
FROM
    base
WHERE
    CAST(fecha_cita AS TIMESTAMP) > TIMESTAMP '2026-06-30 23:59:00'
    AND estado NOT IN ('PENDIENTE', 'PEN')
ORDER BY
    fuente,
    fecha_cita,
    estado;