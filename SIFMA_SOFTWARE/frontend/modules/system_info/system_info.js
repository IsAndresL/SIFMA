// SIFMA — Controlador de Diagnóstico del Sistema
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

export async function initModule() {
    console.log('[SYSTEM_INFO] Solicitando diagnóstico de hardware y software al backend...');

    try {
        const info = await TauriBridge.invoke('get_system_info');
        if (info) {
            if (info.rust_version) {
                document.getElementById('diag-rust').textContent = `Rust ${info.rust_version} (Nativo)`;
            }
            if (info.platform) {
                document.getElementById('diag-os').textContent = info.platform.toUpperCase();
            }
        }
    } catch (err) {
        console.warn('[SYSTEM_INFO] Operando con valores de entorno predeterminados.');
    }
}
