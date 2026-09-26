WITH
    norte AS (
        SELECT
            'NORTE' AS fuente,
            cita_id,
            fecha_creacion,
            fecha_cita,
            fecha_actualizacion
        FROM
            read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
    ),
    sur AS (
        SELECT
            'SUR' AS fuente,
            cita_id,
            fecha_creacion,
            fecha_cita,
            fecha_actualizacion
        FROM
            read_csv_auto ('data/landing/ips_sur_citas.csv', header = true)
    ),
    occidente AS (
        SELECT
            'OCCIDENTE' AS fuente,
            id_cita AS cita_id,
            fecha_creacion,
            fecha_hora_cita AS fecha_cita,
            fecha_actualizacion
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
    CASE
        WHEN CAST(fecha_cita AS TIMESTAMP) > TIMESTAMP '2026-06-30 23:59:00' THEN 1
        ELSE 0
    END AS cita_supera_corte,
    CASE
        WHEN CAST(fecha_creacion AS TIMESTAMP) > TIMESTAMP '2026-06-30 23:59:00' THEN 1
        ELSE 0
    END AS creacion_supera_corte,
    CASE
        WHEN CAST(fecha_actualizacion AS TIMESTAMP) > TIMESTAMP '2026-06-30 23:59:00' THEN 1
        ELSE 0
    END AS actualizacion_supera_corte
FROM
    base
WHERE
    CAST(fecha_creacion AS TIMESTAMP) > TIMESTAMP '2026-06-30 23:59:00'
    OR CAST(fecha_cita AS TIMESTAMP) > TIMESTAMP '2026-06-30 23:59:00'
    OR CAST(fecha_actualizacion AS TIMESTAMP) > TIMESTAMP '2026-06-30 23:59:00'
ORDER BY
    fuente,
    fecha_cita;