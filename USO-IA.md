# USO DE INTELIGENCIA ARTIFICIAL

Declaración del uso de herramientas de IA durante la prueba técnica.

> **Nota:** Este documento solo describe lo que se hizo con herramientas de inteligencia artificial durante la prueba técnica, lo que no se incluya aquí es sinónimo de que no se utilizó IA en esa parte.


## 1. Herramientas utilizadas

| Herramienta | En qué parte del ejercicio la usé | Entregables |
|---|--- |---|
| Copilot | Diseño de la estructura de archivos y directorios adecuados para el proyecto | README.md, USO-IA.md, registro_tiempo.md |
| Claude | Estructurar el SQL de los hallazgos de calidad de datos | 01_diagnostico.ipynb, sql/diagnostico/*.sql |
| Copilot | Diseño de la estructura de archivos y directorios adecuados para el proyecto | src/ |
| Copilot | Generación de pruebas unitarias para la CLI y la ingestión de datos | tests/ |


## 2. Manejo de los datos

### 2.1. Qué información compartí con herramientas externas

- Se le indico los entregables que se esperan en la prueba, así como sus parámetros para el desarrollo, hasta este punto no se ha compartido nada más.
- Para estructurar el SQL, proporcioné la tabla resumen que generé a partir de los los puntos identificados en el desarrollo del notebook, incluyendo los hallazgos, registros afectados, porcentaje sobre la base, base, impacto en negocio y abordaje.
- Se proporciono acceso al repositorio de código para que la IA pudiera analizar la estructura del proyecto y generar las pruebas unitarias correspondientes.

### 2.2. Criterio aplicado

- Solo compartí información necesaria para estructurar el SQL de los hallazgos de calidad de datos, evitando exponer datos sensibles o irrelevantes (teniendo en cuenta que se asume que los datos deben ser tratados como tal).
- No se comparte información sensible ni datos con la IA, solo el repositorio de código y la estructura del proyecto.


## 3. Cómo verifiqué lo que produjo la IA

- La estructura generada por la IA, ha definido una estructura estándar donde se disponen directorios específicos archivos `.sql`y lógica del proceso.
- Verifiqué que los archivos `.sql` generados correspondieran a los hallazgos identificados en el notebook y que la lógica reflejara correctamente la estructura de la tabla resumen.
- Se ejecutan las pruebas unitarias generadas para verificar que la CLI y la ingestión de datos funcionen correctamente.


## 4. Declaración final

Puedo explicar y modificar en vivo todo el contenido de este repositorio.
