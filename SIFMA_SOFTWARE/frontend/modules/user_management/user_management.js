// SIFMA — Controlador de Gestión de Usuarios
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

export async function initModule() {
    console.log('[USER_MANAGEMENT] Cargando directorio de usuarios autorizados...');
    
    const btnAdd = document.getElementById('btn-add-user');
    if (btnAdd) {
        btnAdd.addEventListener('click', () => {
            alert('Formulario de creación de usuario (modal nativo)');
        });
    }
}
