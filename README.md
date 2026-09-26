# PRUEBA TÉCNICA - DON DOCTOR

Repositorio de Github donde voy guardando los avances de la prueba técnica de DonDoctor sobre ausentismo en IPS y clínicas.


## Tabla de contenido

1. [Descripción](#descripción)
2. [Estructura](#estructura)


## Descripción

Este repositorio se construye para reunir, en un solo lugar, todo lo que se vaya produciendo durante la prueba técnica: el código, las consultas, los análisis y los documentos de apoyo.

Por ahora está en una etapa inicial. Lo único que hay es la estructura de carpetas, pensada a partir de la lectura de las instrucciones de la prueba. Todavía no hay código ni resultados.

A medida que avance el trabajo, el repositorio irá creciendo y este documento se irá completando con nuevas secciones.

> **Nota:** Los datos entregados para la prueba no se subirán al repositorio, como buena práctica.


## Estructura

Esta es la propuesta inicial de organización. Se basa en lo que piden las instrucciones de la prueba y puede cambiar a medida que se entiendan mejor los datos y las necesidades del proyecto.

```
technical_test_don_doctor_2026/
├── README.md
├── USO-IA.md
├── .gitignore
├── requirements.txt
├── Makefile
│
├── data/
│   ├── landing/               Archivos originales
│   └── warehouse/             Base DuckDB generada por el pipeline
│
├── sql/
│   ├── diagnostico/           Consultas de E1
│   ├── bronce/
│   ├── plata/
│   └── oro/
│
├── src/
│   ├── config.py              Rutas, parámetros, umbrales
│   ├── ingest/                Carga a bronce
│   ├── transform/             Ejecución de plata y oro
│   ├── quality/               Reglas y pruebas de calidad
│   ├── privacy/               Seudonimización y enmascaramiento
│   └── run_pipeline.py        Punto de entrada único
│
├── tests/                     Pruebas automatizadas (pytest)
│
├── notebooks/
│   ├── 01_diagnostico.ipynb
│   └── 02_modelo_ausentismo.ipynb
│
└── docs/
    ├── hallazgos.md
    ├── reglas_calidad.md
    ├── preguntas_dueno_dato.md
    ├── definicion_ausentismo.md
    ├── arquitectura.md
    ├── registro_tiempo.md
    └── diagramas/
```

### Directorios

- **`data/`**: Los datos de la prueba. Solo se conserva su estructura.
  - **`landing/`**: Archivos tal como fueron enviados.
  - **`warehouse/`**: Base de datos que genera el proyecto al procesar la información.
- **`sql/`**: Consultas en SQL, organizadas por etapa.
  - **`diagnostico/`**: Consultas que respaldan cada hallazgo sobre la calidad de los datos, una por hallazgo.
  - **`bronce/`**: Consultas de la primera capa, donde el dato se guarda tal como llegó.
  - **`plata/`**: Consultas de la segunda capa, donde el dato se limpia y se unifica.
  - **`oro/`**: Consultas de la tercera capa, con las tablas listas para analizar y calcular el ausentismo.
- **`src/`**: Código en Python que ejecuta el proyecto.
  - **`ingest/`**: Código que carga los archivos originales.
  - **`transform/`**: Código que ejecuta las transformaciones de limpieza y consumo.
  - **`quality/`**: Reglas que revisan que los datos sean correctos y que avisan cuando algo se sale de lo esperado.
  - **`privacy/`**: Código que protege los datos personales, por ejemplo ocultando los identificadores de los pacientes.
- **`tests/`**: Pruebas automáticas que verifican que el código funcione como se espera.
- **`notebooks/`**: Cuadernos de trabajo, uno para explorar los datos y otro para construir el modelo de predicción.
- **`docs/`**: Documentos de apoyo en formato de texto: hallazgos, reglas de calidad, preguntas al dueño del dato, definición de ausentismo, arquitectura y registro de tiempo.
  - **`diagramas/`**: Imágenes y esquemas que acompañan a los documentos.