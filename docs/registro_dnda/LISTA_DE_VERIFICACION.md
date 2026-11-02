# SIFMA — Lista de Verificación para Registro de Software ante la DNDA

**Obra:** SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola en Torres Hidropónicas Verticales  
**Versión:** 1.0.0  
**Fecha de verificación:** Noviembre de 2026  
**Autores:** Andrés Felipe Luna Camargo y Cristian David Peña Martínez  
**Titular patrimonial:** `[POR DEFINIR]` (pendiente de formalización con la Universidad del Magdalena)  

---

## 1. Fundamento Legal y Naturaleza del Registro

En la legislación colombiana (Ley 23 de 1982, Decisión Andina 351 de 1993 y Decreto 1360 de 1989), el soporte lógico (software) goza de protección bajo el régimen del **Derecho de Autor** como obra literaria.

- **Efecto declarativo:** El derecho de autor nace con la creación misma de la obra (principio de protección automática). El registro ante la Unidad Administrativa Especial Dirección Nacional de Derecho de Autor (UAE-DNDA) otorga fecha cierta, constituye una presunción de autoría y titularidad ante terceros (*iuris tantum*) y ofrece publicidad jurídica.
- **Costo del trámite:** Es 100% gratuito.
- **Término de respuesta:** Treinta (30) días hábiles contados a partir del día siguiente a la radicación oficial.
- **Plataforma virtual:** Portal oficial de trámites en línea de la DNDA (https://registro.derechodeautor.gov.co/).

---

## 2. Lista de Chequeo Documental y Técnico

Marque con una **X** cada elemento una vez haya sido verificado antes de radicar la solicitud:

### A. Código Fuente (Obra Literaria Depositaria)
- [ ] **Formato admitido:** Archivo de texto plano (`.txt`) o documento `.pdf` generado a partir del código fuente.
- [ ] **Consolidación completa:** Se incluye la totalidad del código interpretable desarrollado por los autores (`local_server/`, `raspi_node/`, `instalacion/`).
- [ ] **Exclusión de terceros:** Se verificó que el archivo consolidado NO contenga librerías externas de terceros (como código fuente interno de Flask, OpenCV, SQLAlchemy), entornos virtuales (`.venv`) ni archivos binarios/imágenes compiladas.
- [ ] **Cabecera de autoría:** Cada archivo fuente contiene la cabecera estándar con los nombres de los autores y el año 2026.
- [ ] **Sintaxis y funcionamiento:** El código se encuentra libre de código comentado muerto, libre de emojis y compila sin advertencias.
- [ ] **Documentos listos:**
  - `docs/codigo_fuente/SIFMA_codigo_fuente_completo.txt`
  - `docs/codigo_fuente/SIFMA_codigo_fuente_completo.pdf`

### B. Descripción del Programa (Memoria Técnica)
- [ ] **Procedimientos detallados:** El documento explica suficientemente el flujo lógico del software, los métodos de cálculo matemático/geométrico (ExG, Otsu, Sobel, Pearson, GDD) y el protocolo de telemetría.
- [ ] **Diagramas de flujo y arquitectura:** Se incluyen diagramas claros de la arquitectura hexagonal, pipeline de visión y ciclo de datos.
- [ ] **Diccionario de datos:** Se describen las tablas y campos del modelo relacional.
- [ ] **Documento listo:**
  - `docs/arquitectura/DOCUMENTO_TECNICO.md`

### C. Material Auxiliar (Manual de Usuario)
- [ ] **Guía de operación:** Manual paso a paso para la instalación, inicio y uso de cada una de las vistas de la plataforma.
- [ ] **Figuras numeradas:** Capturas de pantalla reales, legibles, en alta resolución y con pie descriptivo formal.
- [ ] **Contingencias:** Procedimientos claros para fallas de hardware (puerto COM, cámara CSI, memoria USB).
- [ ] **Documento listo:**
  - `docs/manual_usuario/MANUAL_DE_USUARIO.md`

### D. Información de los Autores y Titularidad
- [ ] **Ficha del formulario completada:** Se han ingresado los datos biográficos de Andrés Felipe Luna Camargo y Cristian David Peña Martínez en `docs/registro_dnda/FICHA_FORMULARIO.md`.
- [ ] **Definición de titularidad patrimonial:** Se ha consensuado con los docentes y la Universidad del Magdalena la titularidad de los derechos patrimoniales:
  - *Opción 1:* Los autores conservan la titularidad patrimonial y licencian su uso a la Universidad.
  - *Opción 2:* Los autores ceden los derechos patrimoniales a la Universidad del Magdalena a cambio de reconocimiento explícito en la patente/modelo de utilidad de la torre o contraprestación académica.
  - *Opción 3:* Cotitularidad compartida (Universidad 50%, Desarrolladores 50%).
- [ ] **Contrato o documento de acuerdo formalizado:** Si la titularidad corresponde a la Universidad o a un tercero, se debe adjuntar copia firmada del documento de cesión o autorización de depósito (`docs/registro_dnda/BORRADOR_CESION_O_AUTORIZACION.md`).

### E. Integridad y Respaldo
- [ ] **Huellas digitales criptográficas:** Se generaron los hashes SHA-256 de todos los archivos del paquete en `docs/registro_dnda/SUMAS_VERIFICACION_SHA256.txt`.
- [ ] **Copia de seguridad local:** Se conserva una copia exacta del paquete en disco óptico o almacenamiento externo inmutable.
