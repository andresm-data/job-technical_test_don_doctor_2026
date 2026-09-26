WITH
    norte AS (
        SELECT
            'NORTE' AS fuente,
            column_name,
            column_type
        FROM
            (
                DESCRIBE
                SELECT
                    *
                FROM
                    read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
            )
    ),
    sur AS (
        SELECT
            'SUR' AS fuente,
            column_name,
            column_type
        FROM
            (
                DESCRIBE
                SELECT
                    *
                FROM
                    read_csv_auto ('data/landing/ips_sur_citas.csv', header = true)
            )
    ),
    occidente AS (
        SELECT
            'OCCIDENTE' AS fuente,
            column_name,
            column_type
        FROM
            (
                DESCRIBE
                SELECT
                    *
                FROM
                    read_csv_auto (
                        'data/landing/ips_occidente_citas.csv',
                        header = true,
                        delim = ';'
                    )
            )
    )
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
ORDER BY
    column_name,
    fuente;