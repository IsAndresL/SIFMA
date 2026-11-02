# SIFMA — Ficha de Datos para el Formulario de Registro DNDA

**Finalidad:** Documento borrador con todos los campos prellenados requeridos por el sistema de radicación virtual de la Dirección Nacional de Derecho de Autor (DNDA) de Colombia (https://registro.derechodeautor.gov.co/).

---

## 1. Datos Generales de la Solicitud

| Campo del Formulario DNDA | Valor a Ingresar |
| :--- | :--- |
| **Tipo de Solicitud:** | Registro de Soporte Lógico (Software) / Obra Literaria |
| **Título de la Obra:** | SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola en Torres Hidropónicas Verticales |
| **Título Corto / Acrónimo:** | SIFMA |
| **Versión:** | 1.0.0 |
| **Año de Creación / Terminación:** | 2026 |
| **País de Origen de la Obra:** | Colombia |
| **¿La obra es Inédita o Publicada?:** | Inédita (No ha sido objeto de edición comercial masiva) |
| **Forma de Creación:** | Obra en colaboración (creada conjuntamente por dos personas naturales) |
| **¿Es obra originaria o derivada?:** | Originaria |
| **¿Obra realizada por encargo laboral?:** | `[POR DEFINIR / COMPLETAR SEGÚN ACUERDO CON UNIMAGDALENA]` |

---

## 2. Descripción de la Obra

### 2.1 Descripción Sucinta (Resumen Ejecutivo para Certificado)
> Plataforma informática para la automatización del fenotipado no destructivo, estimación morfométrica vegetal por visión artificial y telemetría microclimática multivariable en torres hidropónicas verticales. Procesa pares de imágenes cenitales y laterales mediante segmentación en espacios de color HSV, LAB y ExG para cuantificar área foliar, altura de planta, diámetro basal de tallo e índice de salud foliar, correlacionando dichas variables con ocho parámetros fisicoquímicos en tiempo real para generar reportes científicos con firma digital.

### 2.2 Descripción Detallada de Procedimientos y Módulos
> El sistema se compone de dos subsistemas interoperables:
> 1. Subsistema Embebido de Campo (raspi_node): Desarrollado para Raspberry Pi 5, gestiona la captura sincronizada de dos cámaras CSI ortogonales (cenital y lateral) y registra metadatos en unidades USB desmontables mediante un servicio demonio de bajo consumo.
> 2. Servidor Central y Analítica (local_server): Desarrollado en Python bajo arquitectura limpia (Clean Architecture), procesa lotes de imágenes aplicando: a) rotación física automatizada; b) segmentación por Exceso de Verde (ExG), espacio HSV y CIELAB; c) filtro de componentes conexos anti-plantas vecinas; d) operador Sobel horizontal para medición de calibre de tallo en milímetros.
> Integra un motor de persistencia relacional en SQLite con modo WAL concurrente, driver de comunicación por puerto COM serial para recepción de telemetría (pH, conductividad eléctrica, turbidez, oxígeno disuelto, temperatura de agua y aire, humedad relativa y corriente de bomba) y un generador modular de dossiers científicos con cálculo de matrices de Pearson y suite de firma digital biométrica.

---

## 3. Datos de los Autores (Desarrolladores del Código Fuente)

### Autor 1 (Desarrollador Principal)

| Campo | Valor |
| :--- | :--- |
| **Nombres y Apellidos:** | Andrés Felipe Luna Camargo |
| **Tipo de Documento:** | `[COMPLETAR: Cédula de Ciudadanía / C.C.]` |
| **Número de Documento:** | `[COMPLETAR: Número de Identificación]` |
| **Lugar de Expedición:** | `[COMPLETAR: Ciudad / Departamento]` |
| **Fecha de Nacimiento:** | `[COMPLETAR: DD/MM/AAAA]` |
| **Nacionalidad:** | Colombiana |
| **Estado Civil:** | `[COMPLETAR: Soltero / Casado / etc.]` |
| **Dirección de Domicilio:** | `[COMPLETAR: Dirección física de residencia]` |
| **Ciudad / Municipio:** | `[COMPLETAR: Ej. Santa Marta, Magdalena]` |
| **País:** | Colombia |
| **Teléfono Celular:** | `[COMPLETAR: Número de teléfono celular]` |
| **Correo Electrónico:** | `[COMPLETAR: andresfluna03@gmail.com u otro oficial]` |
| **Porcentaje de Participación:** | 50% |

---

### Autor 2 (Desarrollador Coautor)

| Campo | Valor |
| :--- | :--- |
| **Nombres y Apellidos:** | Cristian David Peña Martínez |
| **Tipo de Documento:** | `[COMPLETAR: Cédula de Ciudadanía / C.C.]` |
| **Número de Documento:** | `[COMPLETAR: Número de Identificación]` |
| **Lugar de Expedición:** | `[COMPLETAR: Ciudad / Departamento]` |
| **Fecha de Nacimiento:** | `[COMPLETAR: DD/MM/AAAA]` |
| **Nacionalidad:** | Colombiana |
| **Estado Civil:** | `[COMPLETAR: Soltero / Casado / etc.]` |
| **Dirección de Domicilio:** | `[COMPLETAR: Dirección física de residencia]` |
| **Ciudad / Municipio:** | `[COMPLETAR: Ciudad de residencia]` |
| **País:** | Colombia |
| **Teléfono Celular:** | `[COMPLETAR: Número de teléfono celular]` |
| **Correo Electrónico:** | `[COMPLETAR: Correo electrónico del autor]` |
| **Porcentaje de Participación:** | 50% |

---

## 4. Titularidad de los Derechos Patrimoniales

> [!IMPORTANT]
> Los **derechos morales** (paternidad de la obra e integridad) corresponden de forma perpetua e irrenunciable a los autores: **Andrés Felipe Luna Camargo** y **Cristian David Peña Martínez**.
>
> La titularidad de los **derechos patrimoniales** (reproducción, distribución y explotación comercial) está actualmente catalogada como:
> `[POR DEFINIR SEGÚN ACUERDO ENTRE AUTORES Y UNIVERSIDAD DEL MAGDALENA]`

### Casos a Seleccionar en el Formulario según Resolución:
- **Opción A (Titularidad en cabeza de los autores):** Si los autores radican a nombre propio, se marcan las mismas personas naturales como titulares patrimoniales.
- **Opción B (Cesión a la Universidad del Magdalena):** Se ingresa la Universidad del Magdalena (NIT 891.780.111-8) como persona jurídica titular y se adjunta el contrato de cesión de derechos patrimoniales debidamente suscrito.
- **Opción C (Cotitularidad Universidad - Autores):** Se ingresa la Universidad del Magdalena y los dos autores con los porcentajes convenidos (ej. 50% Universidad, 25% Luna, 25% Peña).

---

## 5. Documentos Anexos Obligatorios para Adjuntar en el Portal

1. **Código Fuente del Software:**
   - Archivo consolidado: `docs/codigo_fuente/SIFMA_codigo_fuente_completo.pdf` (o versión `.txt`).
2. **Memoria Técnica y Descripción de Procedimientos:**
   - Archivo: `docs/arquitectura/DOCUMENTO_TECNICO.md` (convertido a `.pdf`).
3. **Manual de Usuario / Material Auxiliar:**
   - Archivo: `docs/manual_usuario/MANUAL_DE_USUARIO.md` (convertido a `.pdf`).
4. **Contrato de Cesión o Transferencia (Solo si aplica Opción B o C):**
   - Documento firmado: `docs/registro_dnda/BORRADOR_CESION_O_AUTORIZACION.md`.

