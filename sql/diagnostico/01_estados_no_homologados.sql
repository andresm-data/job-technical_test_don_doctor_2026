WITH
    citas_norte AS (
        SELECT
            'NORTE' AS fuente,
            estado AS estado_crudo
        FROM
            read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
    ),
    citas_sur AS (
        SELECT
            'SUR' AS fuente,
            estado AS estado_crudo
        FROM
            read_csv_auto ('data/landing/ips_sur_citas.csv', header = true)
    ),
    citas_occidente AS (
        SELECT
            'OCCIDENTE' AS fuente,
            estado_cita AS estado_crudo
        FROM
            read_csv_auto (
                'data/landing/ips_occidente_citas.csv',
                header = true,
                delim = ';'
            )
    ),
    estados_unificados AS (
        SELECT
            *
        FROM
            citas_norte
        UNION ALL
        SELECT
            *
        FROM
            citas_sur
        UNION ALL
        SELECT
            *
        FROM
            citas_occidente
    )
SELECT
    fuente,
    estado_crudo,
    COUNT(*) AS citas,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (
            PARTITION BY
                fuente
        ),
        2
    ) AS porcentaje_fuente
FROM
    estados_unificados
GROUP BY
    1,
    2
ORDER BY
    fuente,
    citas DESC,
    estado_crudo;