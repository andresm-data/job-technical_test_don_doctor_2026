WITH
    wa AS (
        SELECT
            _id,
            tipo,
            ts,
            json_extract_string (contexto, '$.ips') AS ips,
            json_extract_string (contexto, '$.ref_cita') AS ref_cita,
            mensaje.destinatario AS destinatario
        FROM
            read_json_auto (
                'data/landing/whatsapp_eventos.jsonl',
                format = 'newline_delimited'
            )
    ),
    norte AS (
        SELECT
            cita_id
        FROM
            read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
    ),
    sur AS (
        SELECT
            cita_id
        FROM
            read_csv_auto ('data/landing/ips_sur_citas.csv', header = true)
    ),
    occidente AS (
        SELECT
            id_cita AS cita_id
        FROM
            read_csv_auto (
                'data/landing/ips_occidente_citas.csv',
                header = true,
                delim = ';'
            )
    ),
    citas AS (
        SELECT
            cita_id
        FROM
            norte
        UNION ALL
        SELECT
            cita_id
        FROM
            sur
        UNION ALL
        SELECT
            cita_id
        FROM
            occidente
    )
SELECT
    wa._id,
    wa.ips,
    wa.tipo,
    wa.ts,
    wa.destinatario,
    wa.ref_cita,
    CASE
        WHEN wa.ref_cita IS NULL THEN 'sin_ref_cita'
        WHEN c.cita_id IS NULL THEN 'ref_cita_no_encontrada'
    END AS problema_cruce
FROM
    wa
    LEFT JOIN citas c ON wa.ref_cita = c.cita_id
WHERE
    wa.ref_cita IS NULL
    OR c.cita_id IS NULL
ORDER BY
    problema_cruce,
    ips,
    ts;