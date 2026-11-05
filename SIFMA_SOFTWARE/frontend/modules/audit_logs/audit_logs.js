// SIFMA — Controlador Modular: Auditoría y Seguridad
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Registro de Actividad y Logs de Auditoría';
    if (subheading) subheading.textContent = 'Trazabilidad cronológica de movimientos, modificaciones de cuentas, configuración y operaciones críticas';

    await loadAuditLogs();
    setupEventListeners();
}

async function loadAuditLogs() {
    try {
        const logs = await TauriBridge.invoke('get_audit_logs') || [];
        const tbody = document.getElementById('audit-table-tbody');
        if (!tbody) return;

        let html = '';
        logs.forEach(l => {
            html += `
                <tr>
                    <td><code>#${l.id}</code></td>
                    <td style="font-family: var(--font-mono); font-size: 11.5px;">${l.timestamp}</td>
                    <td><strong>${l.user}</strong></td>
                    <td><span class="badge badge-primary">${l.event_type}</span></td>
                    <td style="font-family: var(--font-mono); font-size: 11.5px;">${l.ip}</td>
                    <td><code>${l.resource}</code></td>
                    <td><span class="badge badge-success">${l.status}</span></td>
                    <td style="font-family: var(--font-mono); font-size: 10.5px; color: var(--text-muted); max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${l.hash}">${l.hash}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('[AUDIT LOGS ERROR]', err);
    }
}

function setupEventListeners() {
    const btn = document.getElementById('btn-refresh-audit');
    if (btn) btn.addEventListener('click', loadAuditLogs);
}
