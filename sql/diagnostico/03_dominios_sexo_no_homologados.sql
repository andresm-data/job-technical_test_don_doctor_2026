WITH
    norte AS (
        SELECT
            'NORTE' AS fuente,
            sexo AS sexo_crudo
        FROM
            read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
    ),
    sur AS (
        SELECT
            'SUR' AS fuente,
            sexo AS sexo_crudo
        FROM
            read_csv_auto ('data/landing/ips_sur_citas.csv', header = true)
    ),
    occidente AS (
        SELECT
            'OCCIDENTE' AS fuente,
            genero AS sexo_crudo
        FROM
            read_csv_auto (
                'data/landing/ips_occidente_citas.csv',
                header = true,
                delim = ';'
            )
    ),
    sexo_unificado AS (
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
    sexo_crudo,
    COUNT(*) AS citas,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (
            PARTITION BY
                fuente
        ),
        2
    ) AS porcentaje_fuente
FROM
    sexo_unificado
GROUP BY
    1,
    2
ORDER BY
    fuente,
    citas DESC,
    sexo_crudo;