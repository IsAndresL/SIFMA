# SIFMA — Instalador Oficial para Windows (SIFMA_Instalador_Setup.exe)
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import base64
import json
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


# Estado global del instalador (fuera de js_api para evitar que PyWebView serialice objetos nativos y congele la ventana)
_INSTALL_STATE = {
    "percent": 0,
    "status": "Preparando instalación...",
    "done": False,
    "error": "",
    "installed_exe": "",
    "install_dir": get_default_install_dir(),
    "data_dir": get_default_data_dir(),
}


def create_windows_shortcut(shortcut_path: str, target_exe: str, working_dir: str, icon_path: str):
    """Crea un acceso directo (.lnk) en Windows de forma silenciosa."""
    ps_script = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{shortcut_path}"); '
        f'$s.TargetPath = "{target_exe}"; '
        f'$s.WorkingDirectory = "{working_dir}"; '
        f'$s.IconLocation = "{icon_path}"; '
        f'$s.Description = "SIFMA Desktop"; '
        f'$s.Save()'
    )
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        creationflags=creation_flags,
        capture_output=True,
    )


class InstallerBridge:
    """Puente ligero JS-Python sin atributos públicos complejos para evitar bloqueos de hilo en WinForms."""

    def select_folder(self, current_path: str = ""):
        """Abre el selector nativo de carpetas de Windows."""
        import webview

        try:
            win = webview.windows[0]
            start_dir = current_path if (current_path and os.path.exists(current_path)) else os.path.expanduser("~")
            result = win.create_file_dialog(webview.FOLDER_DIALOG, directory=start_dir)
            if result and len(result) > 0:
                chosen = result[0]
                if not chosen.lower().endswith("sifma"):
                    chosen = os.path.join(chosen, "SIFMA")
                return {"selected": chosen}
        except Exception:
            pass
        return {"selected": ""}

    def start_installation(self, install_dir: str, data_dir: str, create_desktop: bool, create_start_menu: bool):
        _INSTALL_STATE["percent"] = 5
        _INSTALL_STATE["status"] = "Creando carpetas..."
        _INSTALL_STATE["done"] = False
        _INSTALL_STATE["error"] = ""
        _INSTALL_STATE["install_dir"] = (install_dir or get_default_install_dir()).strip()
        _INSTALL_STATE["data_dir"] = (data_dir or get_default_data_dir()).strip()

        threading.Thread(
            target=_run_install_worker,
            args=(
                _INSTALL_STATE["install_dir"],
                _INSTALL_STATE["data_dir"],
                bool(create_desktop),
                bool(create_start_menu),
            ),
            daemon=True,
        ).start()
        return {"started": True}

    def get_progress(self):
        return {
            "percent": _INSTALL_STATE["percent"],
            "status": _INSTALL_STATE["status"],
            "done": _INSTALL_STATE["done"],
            "error": _INSTALL_STATE["error"],
        }

    def finish_installer(self, launch_now: bool = True):
        exe_path = _INSTALL_STATE.get("installed_exe") or os.path.join(
            _INSTALL_STATE["install_dir"], "SIFMA_Desktop.exe"
        )
        if launch_now and os.path.exists(exe_path):
            try:
                subprocess.Popen([exe_path], cwd=_INSTALL_STATE["install_dir"])
            except Exception:
                pass

        def _close():
            time.sleep(0.2)
            os._exit(0)

        threading.Thread(target=_close, daemon=True).start()
        return {"closing": True}


def _run_install_worker(install_dir: str, data_dir: str, create_desktop: bool, create_start_menu: bool):
    try:
        os.makedirs(install_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "data", "uploads"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "data", "processed"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "data", "telemetry"), exist_ok=True)

        # Guardar preferencia de ruta de datos en %APPDATA%\SIFMA\sifma_paths.json para que SIFMA_Desktop la use siempre
        default_appdata = get_default_data_dir()
        os.makedirs(default_appdata, exist_ok=True)
        with open(os.path.join(default_appdata, "sifma_paths.json"), "w", encoding="utf-8") as cfg_f:
            json.dump({"install_dir": install_dir, "user_data_dir": data_dir}, cfg_f, indent=2)

        _INSTALL_STATE["percent"] = 20
        _INSTALL_STATE["status"] = "Copiando archivos del programa..."

        bundled_exe = os.path.join(RESOURCE_DIR, "payload", "SIFMA_Desktop.exe")
        if not os.path.exists(bundled_exe):
            bundled_exe = os.path.join(RESOURCE_DIR, "dist", "SIFMA_Desktop.exe")

        if not os.path.exists(bundled_exe):
            raise FileNotFoundError("No se encontró el paquete SIFMA_Desktop.exe.")

        installed_exe_path = os.path.join(install_dir, "SIFMA_Desktop.exe")
        _INSTALL_STATE["installed_exe"] = installed_exe_path

        total_size = os.path.getsize(bundled_exe)
        copied = 0
        chunk_size = 1024 * 1024 * 4  # Bloques de 4 MB

        with open(bundled_exe, "rb") as src, open(installed_exe_path, "wb") as dst:
            while True:
                buf = src.read(chunk_size)
                if not buf:
                    break
                dst.write(buf)
                copied += len(buf)
                ratio = min(1.0, copied / max(1, total_size))
                _INSTALL_STATE["percent"] = 20 + int(ratio * 60)
                mb_done = round(copied / (1024 * 1024), 1)
                mb_total = round(total_size / (1024 * 1024), 1)
                _INSTALL_STATE["status"] = f"Instalando SIFMA ({mb_done} / {mb_total} MB)..."

        bundled_ico = os.path.join(RESOURCE_DIR, "static", "img", "sifma_icon.ico")
        target_ico = os.path.join(install_dir, "sifma_icon.ico")
        if os.path.exists(bundled_ico):
            shutil.copy2(bundled_ico, target_ico)
        else:
            target_ico = installed_exe_path

        # Si hay un .env junto al instalador, importarlo
        installer_dir = os.path.dirname(
            os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)
        )
        usb_env = os.path.join(installer_dir, ".env")
        user_env = os.path.join(data_dir, ".env")
        if os.path.exists(usb_env) and not os.path.exists(user_env):
            shutil.copy2(usb_env, user_env)

        if create_desktop:
            _INSTALL_STATE["percent"] = 88
            _INSTALL_STATE["status"] = "Creando acceso directo en el Escritorio..."
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop_dir):
                desktop_dir = os.path.join(os.path.expanduser("~"), "Escritorio")
            if os.path.exists(desktop_dir):
                create_windows_shortcut(
                    os.path.join(desktop_dir, "SIFMA.lnk"),
                    installed_exe_path,
                    install_dir,
                    target_ico,
                )

        if create_start_menu:
            _INSTALL_STATE["percent"] = 95
            _INSTALL_STATE["status"] = "Registrando en Menú Inicio..."
            start_menu_dir = os.path.join(
                os.getenv("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"
            )
            if os.path.exists(start_menu_dir):
                create_windows_shortcut(
                    os.path.join(start_menu_dir, "SIFMA.lnk"),
                    installed_exe_path,
                    install_dir,
                    target_ico,
                )

        _INSTALL_STATE["percent"] = 100
        _INSTALL_STATE["status"] = "Instalación completada"
        _INSTALL_STATE["done"] = True
    except Exception as e:
        _INSTALL_STATE["error"] = str(e)
        _INSTALL_STATE["status"] = "Error en la instalación"


def build_installer_html(install_dir: str, data_dir: str) -> str:
    svg_path = os.path.join(RESOURCE_DIR, "static", "img", "sifma_sin_texto.svg")
    logo_uri = ""
    if os.path.exists(svg_path):
        try:
            with open(svg_path, "rb") as f:
                logo_uri = "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")
        except Exception:
            pass

    logo_tag = f'<img src="{logo_uri}" style="width:46px;height:46px;" />' if logo_uri else "<strong>SIFMA</strong>"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Instalar SIFMA</title>
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
    body {{
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        background: #f8fafc;
        color: #0f172a;
        height: 100vh;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }}
    .header {{
        background: #064e3b;
        color: #ffffff;
        padding: 18px 24px;
        display: flex;
        align-items: center;
        gap: 14px;
    }}
    .logo-box {{
        width: 56px;
        height: 56px;
        border-radius: 12px;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }}
    .header h1 {{
        font-size: 19px;
        font-weight: 700;
        margin-bottom: 2px;
    }}
    .header p {{
        font-size: 12px;
        color: #a7f3d0;
    }}
    .content {{
        flex: 1;
        padding: 20px 24px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 14px;
    }}
    .field-group {{
        display: flex;
        flex-direction: column;
        gap: 5px;
    }}
    .field-label {{
        font-size: 12px;
        font-weight: 600;
        color: #334155;
    }}
    .path-picker {{
        display: flex;
        gap: 8px;
    }}
    .path-input {{
        flex: 1;
        padding: 8px 11px;
        font-size: 12px;
        font-family: Consolas, monospace;
        color: #0f172a;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        outline: none;
    }}
    .path-input:focus {{
        border-color: #059669;
    }}
    .btn-browse {{
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 600;
        background: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        cursor: pointer;
        white-space: nowrap;
    }}
    .btn-browse:hover {{
        background: #e2e8f0;
    }}
    .options-row {{
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 4px;
        padding-top: 10px;
        border-top: 1px solid #e2e8f0;
    }}
    .chk-item {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12.5px;
        color: #334155;
        cursor: pointer;
    }}
    .chk-item input {{
        width: 15px;
        height: 15px;
        accent-color: #059669;
        cursor: pointer;
    }}
    .progress-view {{
        display: none;
        flex-direction: column;
        gap: 12px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 24px 20px;
    }}
    .bar-bg {{
        width: 100%;
        height: 10px;
        background: #e2e8f0;
        border-radius: 99px;
        overflow: hidden;
    }}
    .bar-fill {{
        height: 100%;
        width: 0%;
        background: #059669;
        transition: width 0.2s ease;
    }}
    .footer {{
        padding: 14px 24px;
        background: #ffffff;
        border-top: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
    }}
    .btn {{
        padding: 8px 18px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        border: none;
        cursor: pointer;
    }}
    .btn-primary {{
        background: #059669;
        color: #ffffff;
    }}
    .btn-primary:hover {{ background: #047857; }}
    .btn-secondary {{
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
    }}
</style>
</head>
<body>
    <div class="header">
        <div class="logo-box">{logo_tag}</div>
        <div>
            <h1>SIFMA Desktop</h1>
            <p>Instalación en este equipo</p>
        </div>
    </div>

    <div class="content">
        <div id="view-config" style="display:flex; flex-direction:column; gap:12px;">
            <div class="field-group">
                <span class="field-label">Ubicación del programa:</span>
                <div class="path-picker">
                    <input type="text" id="inp-install-dir" class="path-input" value="{install_dir}" />
                    <button type="button" class="btn-browse" onclick="pickDir('inp-install-dir')">Examinar...</button>
                </div>
            </div>

            <div class="field-group">
                <span class="field-label">Ubicación de base de datos y fotos:</span>
                <div class="path-picker">
                    <input type="text" id="inp-data-dir" class="path-input" value="{data_dir}" />
                    <button type="button" class="btn-browse" onclick="pickDir('inp-data-dir')">Examinar...</button>
                </div>
            </div>

            <div class="options-row">
                <label class="chk-item">
                    <input type="checkbox" id="chk-desktop" checked>
                    <span>Crear acceso directo en el Escritorio</span>
                </label>
                <label class="chk-item">
                    <input type="checkbox" id="chk-startmenu" checked>
                    <span>Agregar al Menú Inicio</span>
                </label>
                <label class="chk-item">
                    <input type="checkbox" id="chk-launch" checked>
                    <span>Iniciar SIFMA al finalizar</span>
                </label>
            </div>
        </div>

        <div id="view-progress" class="progress-view">
            <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600;">
                <span id="lbl-status">Instalando...</span>
                <span id="lbl-pct" style="color:#059669; font-family:Consolas,monospace;">0%</span>
            </div>
            <div class="bar-bg">
                <div id="bar-fill" class="bar-fill"></div>
            </div>
            <div id="lbl-error" style="font-size:12px; color:#dc2626; display:none;"></div>
        </div>
    </div>

    <div class="footer">
        <button type="button" id="btn-cancel" class="btn btn-secondary" onclick="closeSetup(false)">Cancelar</button>
        <button type="button" id="btn-install" class="btn btn-primary" onclick="startInstall()">Instalar</button>
        <button type="button" id="btn-finish" class="btn btn-primary" style="display:none;" onclick="closeSetup(true)">Finalizar</button>
    </div>

    <script>
        var pollTimer = null;

        async function pickDir(inputId) {{
            if (!window.pywebview || !window.pywebview.api) return;
            var cur = document.getElementById(inputId).value;
            var res = await window.pywebview.api.select_folder(cur);
            if (res && res.selected) {{
                document.getElementById(inputId).value = res.selected;
            }}
        }}

        async function startInstall() {{
            var installDir = document.getElementById('inp-install-dir').value;
            var dataDir = document.getElementById('inp-data-dir').value;
            var desk = document.getElementById('chk-desktop').checked;
            var menu = document.getElementById('chk-startmenu').checked;

            document.getElementById('view-config').style.display = 'none';
            document.getElementById('view-progress').style.display = 'flex';
            document.getElementById('btn-install').style.display = 'none';
            document.getElementById('btn-cancel').disabled = true;

            await window.pywebview.api.start_installation(installDir, dataDir, desk, menu);

            pollTimer = setInterval(async function() {{
                var st = await window.pywebview.api.get_progress();
                if (!st) return;
                document.getElementById('bar-fill').style.width = st.percent + '%';
                document.getElementById('lbl-pct').textContent = st.percent + '%';
                document.getElementById('lbl-status').textContent = st.status;

                if (st.error) {{
                    clearInterval(pollTimer);
                    var errEl = document.getElementById('lbl-error');
                    errEl.style.display = 'block';
                    errEl.textContent = st.error;
                    document.getElementById('btn-cancel').disabled = false;
                }} else if (st.done) {{
                    clearInterval(pollTimer);
                    document.getElementById('btn-cancel').style.display = 'none';
                    document.getElementById('btn-finish').style.display = 'inline-block';
                }}
            }}, 150);
        }}

        function closeSetup(isFinish) {{
            var launch = isFinish ? document.getElementById('chk-launch').checked : false;
            if (window.pywebview && window.pywebview.api) {{
                window.pywebview.api.finish_installer(launch);
            }}
        }}
    </script>
</body>
</html>"""


def main():
    import webview

    bridge = InstallerBridge()
    icon_path = os.path.join(RESOURCE_DIR, "static", "img", "sifma_icon.ico")
    html = build_installer_html(_INSTALL_STATE["install_dir"], _INSTALL_STATE["data_dir"])

    webview.create_window(
        title="Instalar SIFMA Desktop",
        html=html,
        js_api=bridge,
        width=540,
        height=395,
        resizable=False,
    )

    if os.path.exists(icon_path):
        webview.start(icon=icon_path)
    else:
        webview.start()


if __name__ == "__main__":
    main()
