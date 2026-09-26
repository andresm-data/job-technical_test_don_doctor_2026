WITH
    wa AS (
        SELECT
            _id,
            tipo,
            ts,
            mensaje.destinatario AS destinatario,
            json_extract_string (contexto, '$.ips') AS ips,
            json_extract_string (contexto, '$.ref_cita') AS ref_cita
        FROM
            read_json_auto (
                'data/landing/whatsapp_eventos.jsonl',
                format = 'newline_delimited'
            )
    )
SELECT
    tipo,
    ips,
    ref_cita,
    destinatario,
    ts,
    COUNT(*) AS repeticiones,
    COUNT(DISTINCT _id) AS ids_distintos
FROM
    wa
GROUP BY
    1,
    2,
    3,
    4,
    5
HAVING
    COUNT(*) > 1
ORDER BY
    repeticiones DESC,
    tipo,
    ips,
    ref_cita,
    ts;