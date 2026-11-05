// SIFMA — Controlador Modular: Galería de Capturas
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let sessions = [];

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Comparador de Procesamiento Digital';
    if (subheading) subheading.textContent = 'Inspección visual antes/después y segmentación para Canastilla #1';

    await loadGallerySessions();
    setupEventListeners();
}

async function loadGallerySessions() {
    try {
        sessions = await TauriBridge.invoke('list_capture_sessions') || [];
        const container = document.getElementById('captures-scroll-row');
        if (!container || !sessions.length) return;

        let html = '';
        sessions.forEach((s, idx) => {
            html += `
                <div class="capture-thumb-card ${idx === 0 ? 'selected' : ''}" data-id="${s.id}" style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 12px; padding: 10px; cursor: pointer; min-width: 170px; box-shadow: var(--shadow-sm); transition: var(--transition-fast);">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; border-radius: 8px; overflow: hidden; height: 75px; background: #090d16; margin-bottom: 8px; border: 1px solid #1e293b;">
                        <img src="core/assets/cenital_1.png" style="width: 100%; height: 100%; object-fit: cover;">
                        <img src="core/assets/sifma_sin_texto.svg" style="width: 100%; height: 100%; object-fit: contain; padding: 4px;">
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 2px;">
                        <span style="font-size: 11.5px; font-weight: 700; color: var(--text-heading);">${s.timestamp}</span>
                        <span class="badge badge-success" style="font-size: 10px; padding: 2px 6px;">MEDIODÍA</span>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;

        container.querySelectorAll('.capture-thumb-card').forEach(card => {
            card.addEventListener('click', () => {
                const sid = Number(card.dataset.id);
                const s = sessions.find(item => item.id === sid);
                if (s) selectSession(s);
            });
        });
    } catch (err) {
        console.error('[GALLERY ERROR]', err);
    }
}

function selectSession(session) {
    setText('gal-session-title', `Comparador de Fenotipado — Captura del ${session.timestamp}`);
    setText('gal-cenital-area', `${session.foliar_area} cm²`);
    setText('gal-lateral-height', `H = ${session.plant_height} cm`);
}

function setupEventListeners() {
    const crossBtn = document.getElementById('btn-goto-cross');
    if (crossBtn && window.sifmaRouter) {
        crossBtn.addEventListener('click', () => {
            window.sifmaRouter.loadModule('cross_analysis');
        });
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.textContent = val;
}
