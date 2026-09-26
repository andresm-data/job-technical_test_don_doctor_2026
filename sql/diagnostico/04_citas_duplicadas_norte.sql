WITH
    norte AS (
        SELECT
            *
        FROM
            read_csv_auto ('data/landing/ips_norte_citas.csv', header = true)
    ),
    duplicados AS (
        SELECT
            cita_id,
            COUNT(*) AS filas_con_misma_cita,
            COUNT(
                DISTINCT hash (
                    paciente_id,
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
                    recordatorio_enviado,
                    confirmada,
                    gestion_recuperacion,
                    coalesce(motivo_cierre, ''),
                    coalesce(observaciones, ''),
                    coalesce(cita_origen_id, '')
                )
            ) AS versiones_detectadas,
            MIN(fecha_actualizacion) AS primera_actualizacion,
            MAX(fecha_actualizacion) AS ultima_actualizacion
        FROM
            norte
        GROUP BY
            1
        HAVING
            COUNT(*) > 1
    )
SELECT
    cita_id,
    filas_con_misma_cita,
    versiones_detectadas,
    CASE
        WHEN versiones_detectadas = 1 THEN 'duplicado_exacto'
        ELSE 'versiones_conflictivas'
    END AS tipo_duplicado,
    primera_actualizacion,
    ultima_actualizacion
FROM
    duplicados
ORDER BY
    tipo_duplicado DESC,
    filas_con_misma_cita DESC,
    cita_id;