// SIFMA — Controlador Modular: Usuarios y Roles
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Control de Acceso y Roles del Sistema';
    if (subheading) subheading.textContent = 'Administración de cuentas, perfiles de investigación y asignación granular de funciones';

    await loadUsers();
}

async function loadUsers() {
    try {
        const users = await TauriBridge.invoke('get_users_list') || [];
        const tbody = document.getElementById('users-table-tbody');
        if (!tbody) return;

        let html = '';
        users.forEach(u => {
            html += `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="user-avatar-circle" style="width: 36px; height: 36px; font-size: 11px; background: linear-gradient(135deg, #059669, #10b981); color: #fff;">
                                ${u.username.substring(0, 2).toUpperCase()}
                            </div>
                            <div>
                                <div style="font-weight: 700; color: var(--text-heading); font-size: 13.5px;">${u.full_name}</div>
                                <div style="font-size: 11.5px; color: var(--text-muted);">@${u.username}</div>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="badge ${u.role === 'ADMINISTRADOR' ? 'badge-primary' : 'badge-success'}">
                            ${u.role}
                        </span>
                    </td>
                    <td>
                        <span class="badge badge-primary" style="font-size: 10.5px; padding: 2px 6px;">
                            ${u.role === 'ADMINISTRADOR' ? 'Acceso Total (Todos los Módulos)' : 'Investigación & Reportes'}
                        </span>
                    </td>
                    <td style="font-size: 12px; color: var(--text-body);">${u.username}@sifma.edu.co</td>
                    <td>
                        <span class="badge ${u.active ? 'badge-success' : 'badge-danger'}">
                            ${u.active ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td style="font-size: 11.5px; font-family: var(--font-mono); color: var(--text-muted);">${u.created_at}</td>
                    <td style="text-align: right;">
                        <button class="btn btn-outline btn-sm" style="padding: 3px 8px; font-size: 11.5px;">
                            <span class="material-icons-round" style="font-size: 14px;">tune</span>
                            <span>Permisos</span>
                        </button>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('[USERS ERROR]', err);
    }
}
