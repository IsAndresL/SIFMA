# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import base64
import os
import socket
import sys
import threading

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


def build_splash_html(target_url: str) -> str:
    """
    Construye la pantalla de carga animada (Splash Screen).
    La transición hacia el servidor interno se realiza desde JavaScript mediante polling asíncrono,
    evitando llamadas cross-thread sobre el hilo gráfico de Windows (WinForms).
    """
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
        else '<div style="font-weight:700;color:#064e3b;">SIFMA</div>'
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>SIFMA</title>
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
    body {{
        width: 100vw;
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f8fafc;
        color: #0f172a;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        overflow: hidden;
    }}
    .splash-card {{
        width: 420px;
        padding: 36px 32px;
        text-align: center;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
    }}
    .logo-ring {{
        width: 88px;
        height: 88px;
        margin: 0 auto 16px;
        border-radius: 20px;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulseLogo 2s infinite ease-in-out;
    }}
    .splash-logo {{
        width: 64px;
        height: 64px;
        display: block;
    }}
    @keyframes pulseLogo {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.04); }}
    }}
    h1 {{
        font-size: 24px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #0f172a;
        margin-bottom: 4px;
    }}
    .subtitle {{
        font-size: 12.5px;
        color: #64748b;
        margin-bottom: 24px;
    }}
    .progress-track {{
        width: 100%;
        height: 6px;
        background: #f1f5f9;
        border-radius: 99px;
        overflow: hidden;
        margin-bottom: 10px;
    }}
    .progress-fill {{
        height: 100%;
        width: 15%;
        background: #059669;
        border-radius: 99px;
        transition: width 0.25s ease;
    }}
    .status-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
        color: #475569;
    }}
    .percent-badge {{
        font-family: Consolas, monospace;
        font-weight: 700;
        color: #059669;
    }}
</style>
</head>
<body>
    <div class="splash-card">
        <div class="logo-ring">{logo_img_tag}</div>
        <h1>SIFMA</h1>
        <div class="subtitle">Fenotipado &amp; Telemetría</div>
        <div class="progress-track">
            <div id="splash-bar" class="progress-fill"></div>
        </div>
        <div class="status-row">
            <span id="splash-status">Iniciando servicios...</span>
            <span id="splash-pct" class="percent-badge">15%</span>
        </div>
    </div>
    <script>
        var targetUrl = "{target_url}";
        var pct = 15;
        var bar = document.getElementById('splash-bar');
        var st = document.getElementById('splash-status');
        var pc = document.getElementById('splash-pct');

        var timer = setInterval(function() {{
            if (pct < 90) {{
                pct += 7;
                bar.style.width = pct + '%';
                pc.textContent = pct + '%';
                if (pct > 45) st.textContent = 'Cargando interfaz y base de datos...';
            }}
            fetch(targetUrl + '/login', {{ mode: 'no-cors', cache: 'no-store' }})
                .then(function() {{
                    clearInterval(timer);
                    bar.style.width = '100%';
                    pc.textContent = '100%';
                    st.textContent = 'Listo';
                    window.location.replace(targetUrl + '/login');
                }})
                .catch(function() {{}});
        }}, 280);
    </script>
</body>
</html>"""


def main():
    import webview

    port = find_available_port(5000)
    local_url = f"http://127.0.0.1:{port}"
    icon_path = os.path.join(RESOURCE_DIR, "static", "img", "sifma_icon.ico")
    splash_html = build_splash_html(local_url)

    server_holder = {"http_server": None}

    def bootstrap_backend():
        try:
            from werkzeug.serving import make_server
            from app import app
            from core.config import config
            from core.logger import logger

            logger.info(f"SIFMA Desktop v{config.APP_VERSION} escuchando en {local_url}")
            http_server = make_server("127.0.0.1", port, app, threaded=True)
            server_holder["http_server"] = http_server
            http_server.serve_forever()
        except Exception as e:
            try:
                from core.logger import logger
                logger.error(f"Error iniciando servidor interno: {e}")
            except Exception:
                pass

    server_thread = threading.Thread(target=bootstrap_backend, daemon=True)
    server_thread.start()

    window = webview.create_window(
        title="SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola",
        html=splash_html,
        width=1380,
        height=860,
        min_size=(1024, 680),
        text_select=True,
    )

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
        webview.start(icon=icon_path)
    else:
        webview.start()


if __name__ == "__main__":
    main()
