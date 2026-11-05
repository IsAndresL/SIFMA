# SIFMA — Asistente Visual de Instalación para Windows (SIFMA_Instalador_Setup.exe)
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import base64
import os
import shutil
import subprocess
import sys
import threading
import time

RESOURCE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def get_default_install_dir() -> str:
    local_appdata = os.getenv("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return os.path.join(local_appdata, "Programs", "SIFMA")


def get_default_data_dir() -> str:
    appdata = os.getenv("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(appdata, "SIFMA")


def create_windows_shortcut(shortcut_path: str, target_exe: str, working_dir: str, icon_path: str):
    """Crea un acceso directo nativo (.lnk) en Windows usando WScript.Shell sin dependencias externas."""
    ps_script = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{shortcut_path}"); '
        f'$s.TargetPath = "{target_exe}"; '
        f'$s.WorkingDirectory = "{working_dir}"; '
        f'$s.IconLocation = "{icon_path}"; '
        f'$s.Description = "SIFMA - Sistema Integral de Fenotipado y Monitoreo Agrícola"; '
        f'$s.Save()'
    )
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        creationflags=creation_flags,
        capture_output=True,
    )


class InstallerBridge:
    def __init__(self):
        self.window = None
        self.install_dir = get_default_install_dir()
        self.data_dir = get_default_data_dir()
        self.installed_exe_path = os.path.join(self.install_dir, "SIFMA_Desktop.exe")

    def _emit_progress(self, percent: int, step_title: str, log_line: str, completed: bool = False, error: str = ""):
        if not self.window:
            return
        safe_title = step_title.replace("'", "\\'")
        safe_log = log_line.replace("\\", "\\\\").replace("'", "\\'")
        safe_err = error.replace("\\", "\\\\").replace("'", "\\'")
        done_js = "true" if completed else "false"
        try:
            self.window.evaluate_js(
                f"window.onInstallerProgress({percent}, '{safe_title}', '{safe_log}', {done_js}, '{safe_err}');"
            )
        except Exception:
            pass

    def start_installation(self, create_desktop: bool = True, create_start_menu: bool = True):
        threading.Thread(
            target=self._run_install_worker,
            args=(create_desktop, create_start_menu),
            daemon=True,
        ).start()
        return {"status": "started"}

    def _run_install_worker(self, create_desktop: bool, create_start_menu: bool):
        try:
            self._emit_progress(8, "Preparando directorios del sistema...", f"Destino: {self.install_dir}")
            time.sleep(0.35)
            os.makedirs(self.install_dir, exist_ok=True)

            self._emit_progress(
                22,
                "Configurando bóveda aislada de base de datos e imágenes...",
                f"Bóveda segura verificada en: {self.data_dir}",
            )
            os.makedirs(os.path.join(self.data_dir, "data", "uploads"), exist_ok=True)
            os.makedirs(os.path.join(self.data_dir, "data", "processed"), exist_ok=True)
            os.makedirs(os.path.join(self.data_dir, "data", "telemetry"), exist_ok=True)
            time.sleep(0.4)

            # Localizar el ejecutable SIFMA_Desktop.exe empaquetado dentro del instalador
            bundled_exe = os.path.join(RESOURCE_DIR, "payload", "SIFMA_Desktop.exe")
            if not os.path.exists(bundled_exe):
                bundled_exe = os.path.join(RESOURCE_DIR, "dist", "SIFMA_Desktop.exe")

            if not os.path.exists(bundled_exe):
                raise FileNotFoundError("No se encontró el paquete ejecutable SIFMA_Desktop.exe dentro del instalador.")

            total_size = os.path.getsize(bundled_exe)
            copied = 0
            chunk_size = 1024 * 1024 * 2  # 2 MB por bloque para animación fluida

            self._emit_progress(30, "Extrayendo e instalando motor SIFMA_Desktop.exe...", "Copiando binarios y librerías de visión artificial...")

            with open(bundled_exe, "rb") as src, open(self.installed_exe_path, "wb") as dst:
                while True:
                    buf = src.read(chunk_size)
                    if not buf:
                        break
                    dst.write(buf)
                    copied += len(buf)
                    ratio = min(1.0, copied / max(1, total_size))
                    pct = 30 + int(ratio * 48)
                    mb_done = round(copied / (1024 * 1024), 1)
                    mb_total = round(total_size / (1024 * 1024), 1)
                    self._emit_progress(
                        pct,
                        f"Instalando SIFMA_Desktop.exe ({mb_done} MB / {mb_total} MB)...",
                        "",
                    )
                    time.sleep(0.03)

            # Copiar ícono oficial
            bundled_ico = os.path.join(RESOURCE_DIR, "static", "img", "sifma_icon.ico")
            target_ico = os.path.join(self.install_dir, "sifma_icon.ico")
            if os.path.exists(bundled_ico):
                shutil.copy2(bundled_ico, target_ico)
            else:
                target_ico = self.installed_exe_path

            # Si el usuario colocó un archivo .env junto al instalador en la USB, importarlo a %APPDATA%\SIFMA\.env
            installer_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
            usb_env = os.path.join(installer_dir, ".env")
            user_env = os.path.join(self.data_dir, ".env")
            if os.path.exists(usb_env) and not os.path.exists(user_env):
                shutil.copy2(usb_env, user_env)
                self._emit_progress(82, "Configuración local importada...", "Archivo .env importado a la bóveda segura.")

            if create_desktop:
                self._emit_progress(86, "Creando acceso directo en el Escritorio...", "Acceso directo registrado en el Escritorio de Windows.")
                desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop_dir):
                    desktop_dir = os.path.join(os.path.expanduser("~"), "Escritorio")
                if os.path.exists(desktop_dir):
                    create_windows_shortcut(
                        os.path.join(desktop_dir, "SIFMA Desktop.lnk"),
                        self.installed_exe_path,
                        self.install_dir,
                        target_ico,
                    )
                time.sleep(0.25)

            if create_start_menu:
                self._emit_progress(94, "Registrando SIFMA en el Menú Inicio...", "Acceso directo añadido a Programas de Windows.")
                start_menu_dir = os.path.join(
                    os.getenv("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"
                )
                if os.path.exists(start_menu_dir):
                    create_windows_shortcut(
                        os.path.join(start_menu_dir, "SIFMA Desktop.lnk"),
                        self.installed_exe_path,
                        self.install_dir,
                        target_ico,
                    )
                time.sleep(0.25)

            self._emit_progress(
                100,
                "¡Instalación completada con éxito!",
                f"SIFMA quedó instalado en {self.install_dir}",
                completed=True,
            )
        except Exception as e:
            self._emit_progress(100, "Error durante la instalación", "", completed=False, error=str(e))

    def finish_installer(self, launch_now: bool = True):
        if launch_now and os.path.exists(self.installed_exe_path):
            try:
                subprocess.Popen([self.installed_exe_path], cwd=self.install_dir)
            except Exception:
                pass

        def _exit_soon():
            time.sleep(0.3)
            os._exit(0)

        threading.Thread(target=_exit_soon, daemon=True).start()
        return {"status": "closing"}


def build_installer_html(install_dir: str, data_dir: str) -> str:
    svg_path = os.path.join(RESOURCE_DIR, "static", "img", "sifma_sin_texto.svg")
    logo_uri = ""
    if os.path.exists(svg_path):
        try:
            with open(svg_path, "rb") as f:
                logo_uri = "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")
        except Exception:
            pass

    logo_tag = f'<img src="{logo_uri}" style="width:54px;height:54px;" />' if logo_uri else "<strong>SIFMA</strong>"
    safe_install = install_dir.replace("\\", "\\\\")
    safe_data = data_dir.replace("\\", "\\\\")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Instalador Oficial de SIFMA Desktop</title>
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
    body {{
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        background: #0f172a;
        color: #f8fafc;
        height: 100vh;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }}
    .wizard-banner {{
        background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
        padding: 22px 28px;
        display: flex;
        align-items: center;
        gap: 18px;
        border-bottom: 1px solid rgba(16, 185, 129, 0.25);
    }}
    .logo-circle {{
        width: 68px;
        height: 68px;
        border-radius: 16px;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
    }}
    .banner-text h1 {{
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #ffffff;
        margin-bottom: 4px;
    }}
    .banner-text p {{
        font-size: 12.5px;
        color: #a7f3d0;
    }}
    .wizard-body {{
        flex: 1;
        padding: 24px 28px;
        overflow-y: auto;
    }}
    .info-box {{
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 16px;
        font-size: 12.5px;
        line-height: 1.5;
    }}
    .path-row {{
        margin-top: 8px;
        font-family: Consolas, monospace;
        font-size: 11.5px;
        color: #34d399;
        background: rgba(15, 23, 42, 0.8);
        padding: 6px 10px;
        border-radius: 6px;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }}
    .checkbox-group {{
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 14px;
    }}
    .checkbox-label {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 13px;
        color: #e2e8f0;
        cursor: pointer;
    }}
    .checkbox-label input {{
        width: 16px;
        height: 16px;
        accent-color: #10b981;
        cursor: pointer;
    }}
    .progress-wrapper {{
        display: none;
        flex-direction: column;
        gap: 12px;
        margin-top: 8px;
    }}
    .progress-bar-outer {{
        width: 100%;
        height: 12px;
        background: #1e293b;
        border-radius: 99px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .progress-bar-inner {{
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, #059669, #10b981, #34d399);
        transition: width 0.25s ease;
    }}
    .log-console {{
        background: #090d16;
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 8px;
        padding: 10px 12px;
        height: 135px;
        overflow-y: auto;
        font-family: Consolas, monospace;
        font-size: 11.5px;
        color: #94a3b8;
        line-height: 1.5;
    }}
    .wizard-footer {{
        padding: 16px 28px;
        background: #090d16;
        border-top: 1px solid rgba(148, 163, 184, 0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .btn {{
        padding: 9px 20px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.15s ease;
    }}
    .btn-primary {{
        background: #059669;
        color: #ffffff;
    }}
    .btn-primary:hover {{ background: #047857; }}
    .btn-secondary {{
        background: #1e293b;
        color: #cbd5e1;
        border: 1px solid rgba(148, 163, 184, 0.25);
    }}
</style>
</head>
<body>
    <div class="wizard-banner">
        <div class="logo-circle">{logo_tag}</div>
        <div class="banner-text">
            <h1>Asistente de Instalación — SIFMA Desktop</h1>
            <p>Sistema Integral de Fenotipado y Monitoreo Agrícola (Versión 1.2.0)</p>
        </div>
    </div>

    <div class="wizard-body">
        <!-- VISTA 1: CONFIGURACIÓN PRE-INSTALACIÓN -->
        <div id="step-welcome">
            <div class="info-box">
                <div><strong>Carpeta de Instalación del Programa:</strong></div>
                <div class="path-row">{safe_install}</div>
                <div style="margin-top: 10px;"><strong>Bóveda Aislada de Base de Datos e Imágenes (Protegida ante actualizaciones):</strong></div>
                <div class="path-row">{safe_data}</div>
            </div>

            <div class="checkbox-group">
                <label class="checkbox-label">
                    <input type="checkbox" id="chk-desktop" checked>
                    <span>Crear ícono de acceso directo en el <strong>Escritorio</strong></span>
                </label>
                <label class="checkbox-label">
                    <input type="checkbox" id="chk-startmenu" checked>
                    <span>Registrar acceso directo en el <strong>Menú Inicio de Windows</strong></span>
                </label>
                <label class="checkbox-label">
                    <input type="checkbox" id="chk-launch" checked>
                    <span>Abrir <strong>SIFMA Desktop</strong> automáticamente al terminar la instalación</span>
                </label>
            </div>
        </div>

        <!-- VISTA 2: PROGRESO ANIMADO DE INSTALACIÓN -->
        <div id="step-progress" class="progress-wrapper">
            <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600;">
                <span id="inst-status-title">Iniciando instalación...</span>
                <span id="inst-pct" style="color:#34d399; font-family:Consolas,monospace;">0%</span>
            </div>
            <div class="progress-bar-outer">
                <div id="inst-bar" class="progress-bar-inner"></div>
            </div>
            <div id="inst-log" class="log-console"></div>
        </div>
    </div>

    <div class="wizard-footer">
        <span style="font-size: 11.5px; color: #64748b;">Instalador Oficial SIFMA &bull; Windows x64</span>
        <div style="display: flex; gap: 10px;">
            <button type="button" id="btn-cancel" class="btn btn-secondary" onclick="cancelSetup()">Cancelar</button>
            <button type="button" id="btn-install" class="btn btn-primary" onclick="beginSetup()">Instalar Ahora</button>
            <button type="button" id="btn-finish" class="btn btn-primary" style="display:none;" onclick="completeSetup()">Finalizar y Abrir SIFMA</button>
        </div>
    </div>

    <script>
        function appendLog(msg) {{
            if (!msg) return;
            var box = document.getElementById('inst-log');
            var line = document.createElement('div');
            line.textContent = '> ' + msg;
            box.appendChild(line);
            box.scrollTop = box.scrollHeight;
        }}

        function beginSetup() {{
            var desk = document.getElementById('chk-desktop').checked;
            var menu = document.getElementById('chk-startmenu').checked;
            document.getElementById('step-welcome').style.display = 'none';
            document.getElementById('step-progress').style.display = 'flex';
            document.getElementById('btn-install').style.display = 'none';
            document.getElementById('btn-cancel').disabled = true;
            appendLog('Iniciando asistente de instalación de SIFMA v1.2.0...');
            if (window.pywebview && window.pywebview.api) {{
                window.pywebview.api.start_installation(desk, menu);
            }}
        }}

        window.onInstallerProgress = function(pct, title, logLine, completed, errorMsg) {{
            document.getElementById('inst-bar').style.width = pct + '%';
            document.getElementById('inst-pct').textContent = pct + '%';
            document.getElementById('inst-status-title').textContent = title;
            if (logLine) appendLog(logLine);
            if (errorMsg) {{
                appendLog('ERROR: ' + errorMsg);
                document.getElementById('btn-cancel').disabled = false;
            }}
            if (completed) {{
                appendLog('¡Instalación finalizada exitosamente!');
                document.getElementById('btn-cancel').style.display = 'none';
                document.getElementById('btn-finish').style.display = 'inline-block';
            }}
        }};

        function completeSetup() {{
            var launch = document.getElementById('chk-launch').checked;
            if (window.pywebview && window.pywebview.api) {{
                window.pywebview.api.finish_installer(launch);
            }}
        }}

        function cancelSetup() {{
            if (window.pywebview && window.pywebview.api) {{
                window.pywebview.api.finish_installer(false);
            }}
        }}
    </script>
</body>
</html>"""


def main():
    import webview

    bridge = InstallerBridge()
    icon_path = os.path.join(RESOURCE_DIR, "static", "img", "sifma_icon.ico")
    html = build_installer_html(bridge.install_dir, bridge.data_dir)

    window = webview.create_window(
        title="Instalador de SIFMA Desktop v1.2.0",
        html=html,
        js_api=bridge,
        width=660,
        height=490,
        resizable=False,
    )
    bridge.window = window

    if os.path.exists(icon_path):
        webview.start(icon=icon_path)
    else:
        webview.start()


if __name__ == "__main__":
    main()

