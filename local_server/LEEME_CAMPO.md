# SIFMA - Guía de Instalación y Despliegue en Campo

Este paquete contiene todo lo necesario para desplegar y ejecutar el **Servidor Local SIFMA** en cualquier computador portátil o estación de trabajo Windows/Linux para trabajo en campo con la torre aeropónica vertical.

---

## 1. Requisitos Previos en el PC
- **Sistema Operativo**: Windows 10/11 o Linux.
- **Python**: Versión 3.10, 3.11, 3.12 o 3.13 instalada con la casilla **"Add Python to PATH"** activada durante la instalación.

---

## 2. Instalación en 1 Solo Clic (Windows)

1. Conecta la antena receptora USB (módulos XBee / RF / UART) o ten a mano los lotes de fotos/CSV.
2. Haz doble clic sobre:
   ```cmd
   Instalar_Dependencias.bat
   ```
   *Este script creará automáticamente el entorno virtual `.venv`, instalará todas las dependencias requeridas y generará el acceso directo con el icono oficial de SIFMA en tu Escritorio.*

---

## 3. Acceso y Ejecución Diaria

Una vez instalado, para iniciar el sistema en cualquier momento tienes dos opciones:

### Opción A (Recomendada):
- Haz doble clic en el acceso directo del Escritorio: **`SIFMA - Servidor Local`**
- El navegador web se abrirá automáticamente en: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### Opción B:
- Haz doble clic en el archivo `Iniciar_Servidor.bat`.

---

## 4. Instalación Manual por Consola (Cualquier Sistema Operativo)

Si prefieres instalar por consola (PowerShell / Terminal / Linux):

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv

# En Windows:
.venv\Scripts\activate
# En Linux:
source .venv/bin/activate

# 2. Instalar requerimientos
pip install --upgrade pip
pip install -r local_server/requirements.txt

# 3. Ejecutar servidor
python local_server/app.py
```

---

## 5. Credenciales de Administrador por Defecto

- **Usuario**: `SIFMA_ADMIN`
- **Contraseña**: `Sifma#Campo2026!`
*(Las credenciales pueden personalizarse en el archivo `.env` antes o después de la siembra inicial).*

---

## 6. Soporte Técnico Directo

Para dudas operativas, fallos en campo o calibración de la torre:
- **WhatsApp**: [+57 312 891 9009](https://wa.me/573128919009) (Ing. Andrés Luna)
- **GitHub**: [https://github.com/IsAndresL/SIFMA](https://github.com/IsAndresL/SIFMA)

## 7. Operación con la Antena en Campo
1. Conecta la antena receptora a cualquier puerto USB del computador (se detecta automáticamente).
2. Entra a la sección **Sensores y Telemetría**.
3. Haz clic en **"Iniciar Captación"** o importa los archivos CSV si trabajas fuera de línea.
4. Las 8 gráficas comenzarán a recibir y graficar los datos en tiempo real:
   - pH Solución
   - Conductividad Eléctrica (µS/cm)
   - Turbidez (NTU)
   - Oxígeno Disuelto (mg/L)
   - Temperatura del Agua (°C)
   - Estado Motor (1/0)
   - Temperatura Exterior (°C)
   - Humedad Relativa Exterior (% HR)
5. Al finalizar, presiona **"Detener Captación"** y descarga el archivo CSV consolidado con el botón **"Descargar CSV"**.
