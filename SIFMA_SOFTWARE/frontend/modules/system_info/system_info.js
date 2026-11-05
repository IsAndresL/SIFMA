// SIFMA — Controlador Modular: Información del Sistema y Créditos
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Información del Sistema';
    if (subheading) subheading.textContent = 'Especificaciones técnicas, créditos, autores y términos de licencia oficial de SIFMA';
}
