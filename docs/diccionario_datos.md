# Diccionario de datos — Extracción Data Hub (piloto)

Extracción realizada el 30 de junio de 2026 a las 23:59 desde las bases transaccionales
de tres IPS clientes y desde la colección de eventos de WhatsApp.

Todas las fechas están en hora local de Colombia.

## Archivos

| Archivo | Origen | Descripción |
|---|---|---|
| ips_norte_citas.csv | SQL Server — base IPS Norte | Citas de la IPS Norte |
| ips_sur_citas.csv | SQL Server — base IPS Sur | Citas de la IPS Sur |
| ips_occidente_citas.csv | SQL Server — base IPS Occidente | Citas de la IPS Occidente |
| whatsapp_eventos.jsonl | MongoDB — colección eventos | Eventos de mensajes de recordatorio |

## Campos de citas

| Campo | Descripción |
|---|---|
| cita_id | Identificador único de la cita |
| paciente_id | Identificador seudonimizado del paciente |
| edad | Edad del paciente al momento de la cita |
| sexo | F / M |
| regimen | Régimen de afiliación en salud |
| localidad | Localidad de residencia del paciente |
| especialidad | Especialidad de la cita |
| medico_id | Profesional asignado |
| sede | Sede de atención |
| canal_agendamiento | Canal por el que se creó la cita |
| fecha_creacion | Momento en que se agendó la cita |
| fecha_cita | Fecha y hora programada de la cita |
| fecha_actualizacion | Última modificación del registro |
| estado | PENDIENTE, CONFIRMADA, ATENDIDA, NO_ASISTIO, CANCELADA |
| recordatorio_enviado | 1 si se envió recordatorio |
| confirmada | 1 si el paciente confirmó |
| gestion_recuperacion | Indicador de gestión de la cita |
| motivo_cierre | Motivo de cierre de la cita |
| observaciones | Notas del agendamiento |
| cita_origen_id | Referencia a otra cita |

## Eventos de WhatsApp

Documentos JSON con el evento del mensaje, su marca de tiempo y el contexto de la cita.
