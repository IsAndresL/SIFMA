# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import base64
import os
import socket
import sys
import threading
import time
import urllib.request

# 1. Activar modo escritorio antes de importar la configuración de SIFMA
os.environ["SIFMA_DESKTOP_MODE"] = "1"

# 2. En modo ejecutable sin consola (windowed), redirigir stdout/stderr a archivo de log seguro
if sys.stdout is None or sys.stderr is None:
    try:
        appdata_dir = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "SIFMA")
        os.makedirs(appdata_dir, exist_ok=True)
        stream_log = open(
            os.path.join(appdata_dir, "sifma_runtime.log"), "a", encoding="utf-8", buffering=1
        )
        if sys.stdout is None:
            sys.stdout = stream_log
        if sys.stderr is None:
            sys.stderr = stream_log
    except Exception:
        pass

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

RESOURCE_DIR = getattr(sys, "_MEIPASS", SERVER_DIR) if getattr(sys, "frozen", False) else SERVER_DIR


def find_available_port(preferred_port: int = 5000) -> int:
    """Intenta usar el puerto 5000; si está ocupado, asigna un puerto local libre automáticamente."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred_port)) != 0:
            return preferred_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_server_ready(url: str, timeout_sec: float = 12.0) -> bool:
    """Espera a que el motor interno Flask responda antes de transicionar desde el Splash Screen."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status in (200, 302):
                    return True
        except Exception:
            time.sleep(0.08)
    return False


def build_splash_html() -> str:
    """Construye la pantalla de carga animada (Splash Screen) con el emblema oficial SIFMA."""
    svg_path = os.path.join(RESOURCE_DIR, "static", "img", "sifma_sin_texto.svg")
    logo_data_uri = ""
    if os.path.exists(svg_path):
        try:
            with open(svg_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
                logo_data_uri = f"data:image/svg+xml;base64,{b64}"
        except Exception:
            pass

    logo_img_tag = (
        f'<img src="{logo_data_uri}" alt="SIFMA" class="splash-logo" />'
        if logo_data_uri
        else '<div class="splash-logo-fallback">SIFMA</div>'
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Iniciando SIFMA...</title>
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
    body {{
        width: 100vw;
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at 50% 35%, #132a1f 0%, #091510 70%, #050b08 100%);
        color: #f8fafc;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        overflow: hidden;
    }}
    .splash-card {{
        width: 460px;
        padding: 40px 36px;
        text-align: center;
        background: rgba(15, 29, 22, 0.78);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 18px;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.65), 0 0 40px rgba(5, 150, 105, 0.12);
    }}
    .logo-ring {{
        width: 104px;
        height: 104px;
        margin: 0 auto 20px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.96);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.18), 0 12px 28px rgba(0, 0, 0, 0.45);
        animation: pulseRing 2.2s infinite ease-in-out;
    }}
    .splash-logo {{
        width: 78px;
        height: 78px;
        display: block;
    }}
    @keyframes pulseRing {{
        0%, 100% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.18); }}
        50% {{ transform: scale(1.04); box-shadow: 0 0 0 12px rgba(16, 185, 129, 0.06); }}
    }}
    h1 {{
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 2.5px;
        color: #ffffff;
        margin-bottom: 6px;
    }}
    .subtitle {{
        font-size: 12.5px;
        color: #94a3b8;
        font-weight: 500;
        margin-bottom: 28px;
        line-height: 1.4;
    }}
    .progress-track {{
        width: 100%;
        height: 7px;
        background: rgba(255, 255, 255, 0.09);
        border-radius: 99px;
        overflow: hidden;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .progress-fill {{
        height: 100%;
        width: 18%;
        background: linear-gradient(90deg, #059669, #10b981, #34d399);
        border-radius: 99px;
        transition: width 0.35s cubic-bezier(0.22, 1, 0.36, 1);
    }}
    .status-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
        color: #cbd5e1;
    }}
    .percent-badge {{
        font-family: Consolas, monospace;
        font-weight: 700;
        color: #34d399;
    }}
    .footer-meta {{
        margin-top: 24px;
        padding-top: 14px;
        border-top: 1px solid rgba(255, 255, 255, 0.07);
        font-size: 11px;
        color: #64748b;
    }}
</style>
</head>
<body>
    <div class="splash-card">
        <div class="logo-ring">
            {logo_img_tag}
        </div>
        <h1>SIFMA</h1>
        <div class="subtitle">Sistema Integral de Fenotipado y Monitoreo Agrícola</div>
        <div class="progress-track">
            <div id="splash-bar" class="progress-fill"></div>
        </div>
        <div class="status-row">
            <span id="splash-status">Inicializando entorno nativo de escritorio...</span>
            <span id="splash-pct" class="percent-badge">18%</span>
        </div>
        <div class="footer-meta">
            Bóveda de datos local aislada y protegida &bull; SIFMA Desktop 2026
        </div>
    </div>
    <script>
        window.updateSplash = function(pct, msg) {{
            var bar = document.getElementById('splash-bar');
            var st = document.getElementById('splash-status');
            var pc = document.getElementById('splash-pct');
            if (bar) bar.style.width = pct + '%';
            if (st) st.textContent = msg;
            if (pc) pc.textContent = pct + '%';
        }};
    </script>
</body>
</html>"""


def main():
    import webview

    icon_path = os.path.join(RESOURCE_DIR, "static", "img", "sifma_icon.ico")
    splash_html = build_splash_html()

    window = webview.create_window(
        title="SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola",
        html=splash_html,
        width=1380,
        height=860,
        min_size=(1024, 680),
        text_select=True,
    )

    server_holder = {"http_server": None}

    def update_splash_ui(pct: int, text: str):
        try:
            safe_text = text.replace("'", "\\'")
            window.evaluate_js(f"if(window.updateSplash) window.updateSplash({pct}, '{safe_text}');")
        except Exception:
            pass

    def bootstrap_backend():
        try:
            time.sleep(0.15)
            update_splash_ui(35, "Cargando motor de visión computacional y base de datos...")

            from werkzeug.serving import make_server
            from app import app
            from core.config import config
            from core.logger import logger

            update_splash_ui(68, "Verificando bóveda de datos protegida (%APPDATA%\\SIFMA)...")
            port = find_available_port(5000)
            local_url = f"http://127.0.0.1:{port}"

            logger.info("==========================================================")
            logger.info(f"Iniciando SIFMA Desktop v{config.APP_VERSION}")
            logger.info(f"Bóveda de datos protegida: {config.USER_DATA_DIR}")
            logger.info(f"Base de datos activa: {config.DB_PATH}")
            logger.info(f"Motor interno escuchando en: {local_url}")
            logger.info("==========================================================")

            http_server = make_server("127.0.0.1", port, app, threaded=True)
            server_holder["http_server"] = http_server
            server_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
            server_thread.start()

            update_splash_ui(90, "Iniciando servicios analíticos y telemetría...")
            wait_for_server_ready(f"{local_url}/login")

            update_splash_ui(100, "¡Sistema listo! Abriendo plataforma...")
            time.sleep(0.25)
            window.load_url(local_url)
        except Exception as exc:
            update_splash_ui(100, f"Error al iniciar motor interno: {exc}")

    def on_closed():
        srv = server_holder.get("http_server")
        if srv is not None:
            try:
                srv.shutdown()
            except Exception:
                pass
        os._exit(0)

    window.events.closed += on_closed

    if os.path.exists(icon_path):
        webview.start(bootstrap_backend, icon=icon_path)
    else:
        webview.start(bootstrap_backend)


if __name__ == "__main__":
    main()
