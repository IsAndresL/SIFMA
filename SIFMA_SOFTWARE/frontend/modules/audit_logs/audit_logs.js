// SIFMA — Controlador Modular: Auditoría y Seguridad
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

export async function initModule() {
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = 'Auditoría Forense y Sellado Criptográfico';

    await loadAuditLogs();
    setupEventListeners();
}

async function loadAuditLogs() {
    try {
        const logs = await TauriBridge.invoke('get_audit_logs') || [];
        const tbody = document.getElementById('audit-tbody');
        if (!tbody) return;

        let html = '';
        logs.forEach(l => {
            html += `
                <tr>
                    <td class="font-mono">#${l.id}</td>
                    <td class="font-mono">${l.timestamp}</td>
                    <td><strong>${l.user}</strong></td>
                    <td><span class="badge badge-sky">${l.event_type}</span></td>
                    <td class="font-mono">${l.ip}</td>
                    <td><code>${l.resource}</code></td>
                    <td><span class="badge badge-emerald">${l.status}</span></td>
                    <td class="hash-cell" title="${l.hash}">${l.hash}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    } catch (err) {
        console.error('[AUDIT ERROR]', err);
    }
}

function setupEventListeners() {
    const refreshBtn = document.getElementById('btn-refresh-logs');
    if (refreshBtn) refreshBtn.addEventListener('click', loadAuditLogs);
}
