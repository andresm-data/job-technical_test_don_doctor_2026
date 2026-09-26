WITH
    wa AS (
        SELECT DISTINCT
            json_extract_string (contexto, '$.ref_cita') AS ref_cita
        FROM
            read_json_auto (
                'data/landing/whatsapp_eventos.jsonl',
                format = 'newline_delimited'
            )
        WHERE
            json_extract_string (contexto, '$.ref_cita') IS NOT NULL
    ),
    norte AS (
        SELECT
            'NORTE' AS fuente,
            cita_id,
            estado,
            recordatorio_enviado,
            confirmada
        FROM
            read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
    ),
    sur AS (
        SELECT
            'SUR' AS fuente,
            cita_id,
            estado,
            recordatorio_enviado,
            confirmada
        FROM
            read_csv_auto ('data/landing/ips_sur_citas.csv', header = true)
    ),
    occidente AS (
        SELECT
            'OCCIDENTE' AS fuente,
            id_cita AS cita_id,
            estado_cita AS estado,
            recordatorio_enviado,
            confirmada
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
    estado,
    recordatorio_enviado,
    confirmada
FROM
    base b
    LEFT JOIN wa ON b.cita_id = wa.ref_cita
WHERE
    recordatorio_enviado = 1
    AND wa.ref_cita IS NULL
ORDER BY
    fuente,
    cita_id;