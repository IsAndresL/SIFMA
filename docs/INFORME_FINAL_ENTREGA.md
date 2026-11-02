# SIFMA — Informe Final de Cierre y Paquete de Depósito ante la DNDA

**Proyecto:** SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola en Torres Hidropónicas Verticales  
**Versión Final de Entrega:** 1.0.0  
**Fecha de Cierre:** 2 de noviembre de 2026  
**Rama de Entrega:** `preparacion-registro`  
**Etiqueta de Versión Git:** `v1.0.0-registro`  
**Autores (Desarrolladores del Código):**  
- Andrés Felipe Luna Camargo  
- Cristian David Peña Martínez  
**Titular de los Derechos Patrimoniales:** `[POR DEFINIR]` (Pendiente de formalización con la Universidad del Magdalena)  

---

## 1. Resumen Ejecutivo del Proceso de Preparación

El proyecto SIFMA ha sido sometido a un proceso metódico de auditoría, limpieza, reestructuración y generación documental para su depósito formal como soporte lógico (software) ante la Dirección Nacional de Derecho de Autor (DNDA) de Colombia, bajo los mandatos de la Ley 23 de 1982, la Decisión Andina 351 de 1993 y el Decreto 1360 de 1989.

Se completaron satisfactoriamente las 5 fases de trabajo definidas:
- **Fase 0:** Establecimiento de la línea base, etiquetado inicial `base-previa-limpieza`, inventario técnico completo y captura de 13 pantallas en alta resolución (1920&times;1080).
- **Fase 1:** Normalización de cabeceras oficiales de autoría en 108 archivos de código, eliminación de 73 comentarios redundantes y verificación matemática de identidad exacta del AST (Abstract Syntax Tree) en el 100% de los módulos Python.
- **Fase 2:** Eliminación de 9 módulos legacy en desuso (`database.py`, `blueprints/`, `services/`), desvinculación de `sifma.db` del control de versiones de Git, refuerzo de `.gitignore` y fijación estricta de las 8 dependencias reales en `requirements.txt`.
- **Fase 3:** Reorganización del flujo asistido de instalación en Windows (`instalacion/1_instalar_dependencias/`, `instalacion/2_iniciar_servidor/`, `instalacion/3_crear_acceso_directo/`) y reescritura técnica del `README.md` principal sin emojis.
- **Fase 4:** Elaboración del paquete documental completo: Documento Técnico de Arquitectura, Manual de Usuario formal con figuras reales numeradas, código fuente consolidado en texto y PDF, y paquete de trámite legal DNDA.
- **Fase 5:** Verificación de no regresión en todas las rutas y el pipeline de visión, auditoría de estilo, generación de hashes criptográficos SHA-256 y etiquetado final.

---

## 2. Comparativa del Estado del Proyecto (Antes vs. Después)

| Parámetro Evaluado | Estado Inicial (Fase 0) | Estado Final (Fase 5) | Variación Neta / Impacto |
| :--- | :---: | :---: | :--- |
| **Rama de Trabajo** | `main` (desordenada) | `preparacion-registro` | Rama aislada y trazable por commits |
| **Archivos Propios Rastreados en Git** | 108 archivos | 99 archivos | -9 archivos legacy innecesarios eliminados |
| **Líneas de Código Fuente Consolidado** | 17.926 líneas | 24.218 líneas (con docs) | 100% con cabeceras de autoría DNDA |
| **Comentarios Redundantes / Obvios** | 73 comentarios | 0 comentarios | Código profesional y limpio |
| **Docstrings y Comentarios Científicos** | Conservados | 100% Preservados | Fórmulas ExG, Sobel, Pearson, GDD intactas |
| **Emojis en Código, UI y Documentación** | Presentes en varias vistas | **0 (Cero absoluto)** | Estilo sobrio y académico |
| **Base de Datos en Git (`sifma.db`)** | Rastreada indebidamente | **Desvinculada (`.gitignore`)** | Autogeneración en frío 100% probada |
| **Dependencias en `requirements.txt`** | 14 paquetes (500MB+ extra) | **8 paquetes fijados (`==`)** | Eliminadas dependencias infladas |
| **Flujo de Instalación en Windows** | Scripts sueltos en subcarpeta | **Carpetas 1, 2, 3 numeradas** | Instalación accesible para evaluadores |

---

## 3. Inventario de Entregables para la DNDA

Todos los documentos requeridos para el trámite se encuentran generados y organizados en el directorio `docs/`:

```text
docs/
|-- arquitectura/
|   `-- DOCUMENTO_TECNICO.md             Memoria tecnica y descripcion detallada de procedimientos
|-- manual_usuario/
|   `-- MANUAL_DE_USUARIO.md             Manual formal con 13 figuras reales numeradas
|-- codigo_fuente/
|   |-- SIFMA_codigo_fuente_completo.txt Codigo fuente unificado con indice y lineas numeradas
|   |-- SIFMA_codigo_fuente_completo.pdf Codigo fuente maquetado en PDF para deposito oficial
|   `-- generar_codigo_fuente.py         Script reproducible de consolidacion
|-- registro_dnda/
|   |-- FICHA_FORMULARIO.md              Campos prellenados para el portal de la DNDA
|   |-- LISTA_DE_VERIFICACION.md         Lista de chequeo previa al envio
|   |-- BORRADOR_CESION_O_AUTORIZACION.md Minuta legal de cesion o acuerdo con la Universidad
|   |-- SUMAS_VERIFICACION_SHA256.txt    Hashes criptograficos para fecha cierta e integridad
|   `-- generar_hashes.py                Script generador de sumas SHA-256
`-- _trabajo/                            Evidencias de trabajo, auditorias y capturas base
```

---

## 4. Instrucciones Paso a Paso para Radicar la Solicitud ante la DNDA

El trámite es **completamente gratuito** y se realiza de forma 100% virtual:

1. **Crear o Ingresar a la Cuenta en el Portal DNDA:**
   - Ingrese a: [https://registro.derechodeautor.gov.co/](https://registro.derechodeautor.gov.co/).
   - Si no tiene cuenta, regístrese como Persona Natural (usuario individual de Andrés Luna o Cristian Peña).
2. **Iniciar una Nueva Solicitud:**
   - Seleccione la opción: **"Inscripción de Obra"** -> **"Soporte Lógico (Software)"**.
3. **Paso 1 del Portal - Datos del Solicitante:**
   - Diligencie los datos personales de quien radica la solicitud.
4. **Paso 2 del Portal - Datos de los Autores:**
   - Copie y pegue los datos desde [`docs/registro_dnda/FICHA_FORMULARIO.md`](registro_dnda/FICHA_FORMULARIO.md) (Sección 3).
   - Ingrese como primer autor a **Andrés Felipe Luna Camargo** (50%).
   - Ingrese como segundo autor a **Cristian David Peña Martínez** (50%).
5. **Paso 3 del Portal - Datos del Titular:**
   - Si se radica a nombre propio de los autores: ingrese nuevamente a ambos autores como titulares.
   - Si se radica a nombre de la Universidad del Magdalena: ingrese los datos de la Universidad (NIT 891.780.111-8) y adjunte el contrato de cesión firmado.
6. **Paso 4 del Portal - Datos de la Obra:**
   - **Título:** `SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola en Torres Hidropónicas Verticales`
   - **Año de creación:** `2026`
   - **Carácter:** Inédita, en colaboración, originaria.
   - **Descripción sucinta:** Copie el texto de la Sección 2.1 de `FICHA_FORMULARIO.md`.
7. **Paso 5 del Portal - Adjuntar Archivos:**
   - **Código fuente:** Adjunte `docs/codigo_fuente/SIFMA_codigo_fuente_completo.pdf` (o `.txt`).
   - **Descripción del programa:** Adjunte `docs/arquitectura/DOCUMENTO_TECNICO.md` (guardado como PDF).
   - **Material auxiliar:** Adjunte `docs/manual_usuario/MANUAL_DE_USUARIO.md` (guardado como PDF).
   - **Documento de transferencia:** Adjunte el acuerdo firmado si aplica cesión de derechos patrimoniales.
8. **Finalizar y Radicar:**
   - Envíe la solicitud y guarde el **Número de Radicado** oficial generado por el sistema. La DNDA responderá en un plazo máximo de 30 días hábiles emitiendo el certificado oficial de registro de soporte lógico.

---

## 5. Decisiones Pendientes que el Titular y los Autores Deben Resolver

Antes de presionar el botón de radicación final en el portal de la DNDA, se deben definir tres puntos:

1. **Definición de la Titularidad Patrimonial:**
   - Decidir formalmente si los derechos patrimoniales se radican a nombre de los autores (Andrés Luna y Cristian Peña) o si se celebra la cesión / cotitularidad con la Universidad del Magdalena utilizando la minuta [`docs/registro_dnda/BORRADOR_CESION_O_AUTORIZACION.md`](registro_dnda/BORRADOR_CESION_O_AUTORIZACION.md).
2. **Completar Datos Personales:**
   - Rellenar en `FICHA_FORMULARIO.md` los marcadores `[COMPLETAR]` con los números de cédula, direcciones físicas de residencia, teléfonos celulares y correos oficiales de ambos autores.
3. **Decisión sobre las Variantes Gráficas de Logotipos:**
   - Decidir si se conservan o se eliminan los 5 archivos gráficos alternativos listados como `[DUDA: consultar titular]` en `docs/_trabajo/inventario_limpieza.md` (`sifma_con_texto.svg`, `sifma_logo.svg`, `sin texto blanco.svg`, etc.).
