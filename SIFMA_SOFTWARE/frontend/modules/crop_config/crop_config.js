// SIFMA — Controlador Modular: Configuración de Cultivos
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let profiles = [];

export async function initModule() {
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = 'Configuración de Perfiles y Umbrales del Cultivo';

    await loadProfiles();
    setupEventListeners();
}

async function loadProfiles() {
    try {
        profiles = await TauriBridge.invoke('get_crop_profiles') || [];
        const select = document.getElementById('select-crop-profile');
        if (!select || !profiles.length) return;

        select.innerHTML = profiles.map(p => 
            `<option value="${p.id}" ${p.active ? 'selected' : ''}>${p.name}</option>`
        ).join('');

        populateForm(profiles.find(p => p.active) || profiles[0]);
    } catch (err) {
        console.error('[PROFILES ERROR]', err);
    }
}

function populateForm(profile) {
    if (!profile) return;

    setVal('inp-temp-min', profile.temp_min);
    setVal('inp-temp-opt', profile.temp_opt);
    setVal('inp-temp-max', profile.temp_max);
    setVal('inp-ph-min', profile.ph_min);
    setVal('inp-ph-max', profile.ph_max);
    setVal('inp-ec-min', profile.ec_min);
    setVal('inp-ec-max', profile.ec_max);

    setText('crop-sci-name', profile.name.split('(')[1]?.replace(')', '') || profile.name);
    setText('crop-cycle-days', `${profile.cycle_days} días`);

    const badge = document.getElementById('crop-status-badge');
    if (badge) {
        if (profile.active) {
            badge.className = 'badge badge-emerald';
            badge.textContent = 'ACTIVO EN TORRE';
        } else {
            badge.className = 'badge badge-sky';
            badge.textContent = 'DISPONIBLE';
        }
    }
}

function setupEventListeners() {
    const select = document.getElementById('select-crop-profile');
    if (select) {
        select.addEventListener('change', (e) => {
            const p = profiles.find(item => item.id === Number(e.target.value));
            if (p) populateForm(p);
        });
    }

    const saveBtn = document.getElementById('btn-save-crop-profile');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Guardando...';
            try {
                // Simulación o llamada Tauri
                setTimeout(() => {
                    saveBtn.disabled = false;
                    saveBtn.textContent = 'Guardado Correctamente';
                    setTimeout(() => { saveBtn.textContent = 'Guardar Parámetros'; }, 2000);
                }, 400);
            } catch (err) {
                console.error(err);
                saveBtn.disabled = false;
            }
        });
    }
}

function setVal(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.value = val;
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.textContent = val;
}
