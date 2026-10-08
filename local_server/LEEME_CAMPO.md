# SIFMA - Guía de Instalación y Despliegue en Campo

Este paquete contiene todo lo necesario para ejecutar el **Servidor Local SIFMA** en cualquier computador portátil o estación de trabajo Windows/Linux para trabajo en campo.

---

## 1. Requisitos Previos en el PC
- **Sistema Operativo**: Windows 10/11 o Linux.
- **Python**: Versión 3.10, 3.11, 3.12 o 3.13 instalada con la casilla **"Add Python to PATH"** activada.

---

## 2. Instalación en 1 Solo Clic (Windows)

1. Conecta el PC receptor a la antena USB (XBee PRO S2B).
2. Haz doble clic en:
   ```cmd
   Instalar_Dependencias.bat
   ```
   *Este script creará el entorno virtual `.venv`, actualizará pip e instalará todas las librerías necesarias automáticamente.*

---

## 3. Instalación Manual por Consola (Cualquier Sistema)

Si prefieres instalar por consola (PowerShell / Terminal):

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
```

---

## 4. Iniciar el Servidor en Campo

### Opción Rápida (Windows):
Haz doble clic en:
```cmd
Iniciar_Servidor.bat
```

### Opción por Consola:
```bash
python local_server/app.py
```

Abre tu navegador web e ingresa a:
- **Localmente**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Desde la red WiFi local**: `http://<IP-DEL-PC>:5000`

---

## 5. Credenciales de Acceso por Defecto
- **Usuario**: `admin`
- **Contraseña**: `sifma2026`

---

## 6. Operación con la Antena en Campo
1. Conecta la antena al puerto USB (se detecta automáticamente en `COM6` u otros puertos COM).
2. Entra a la sección **Sensores y Telemetría**.
3. Haz clic en **"Iniciar Captación"** cuando comience el muestreo en la torre.
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
