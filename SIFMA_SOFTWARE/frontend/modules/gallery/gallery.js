// SIFMA — Controlador Modular: Galería Histórica
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let allSessions = [];

export async function initModule() {
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = 'Galería Histórica de Fenotipado y Capturas';

    await loadGalleryItems();
    setupEventListeners();
}

async function loadGalleryItems() {
    try {
        const data = await TauriBridge.invoke('list_capture_sessions');
        allSessions = data || [];
        renderGallery(allSessions);
    } catch (err) {
        console.error('[GALLERY ERROR]', err);
    }
}

function renderGallery(sessions) {
    const container = document.getElementById('gallery-items-container');
    const counter = document.getElementById('gallery-count');
    if (!container) return;

    if (counter) counter.textContent = sessions.length;

    if (!sessions.length) {
        container.innerHTML = '<p style="color: var(--text-muted); padding: 20px;">No hay capturas registradas con los filtros actuales.</p>';
        return;
    }

    let html = '';
    sessions.forEach(s => {
        html += `
            <div class="gallery-card" data-id="${s.id}">
                <div class="card-img-wrap">
                    <img src="core/assets/sifma_sin_texto.svg" alt="Planta #${s.plant_id}">
                    <span class="card-badge-plant">Planta #${s.plant_id}</span>
                    <span class="card-badge-date">${s.timestamp}</span>
                </div>
                <div class="card-info">
                    <div class="card-title-row">
                        <span class="card-title-text">Sesión #${s.id}</span>
                        <span class="badge badge-emerald">${s.health_index}% Salud</span>
                    </div>
                    <div class="card-bio-summary">
                        <span>Área: <strong class="font-mono text-emerald">${s.foliar_area} cm²</strong></span>
                        <span>Altura: <strong class="font-mono">${s.plant_height} cm</strong></span>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;

    // Click handler para abrir modal
    container.querySelectorAll('.gallery-card').forEach(card => {
        card.addEventListener('click', () => {
            const sid = Number(card.dataset.id);
            const found = allSessions.find(item => item.id === sid);
            if (found) openModal(found);
        });
    });
}

function openModal(session) {
    const modal = document.getElementById('gallery-modal');
    if (!modal) return;

    document.getElementById('modal-plant-title').textContent = `Captura Fenotípica — Planta #${session.plant_id}`;
    document.getElementById('modal-date-sub').textContent = `${session.timestamp} — Sesión ID: ${session.id}`;
    document.getElementById('modal-bio-area').textContent = `${session.foliar_area} cm²`;
    document.getElementById('modal-bio-height').textContent = `${session.plant_height} cm`;
    document.getElementById('modal-bio-stem').textContent = `${session.stem_diameter} mm`;
    document.getElementById('modal-bio-health').textContent = `${session.health_index}%`;

    modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.getElementById('gallery-modal');
    if (modal) modal.style.display = 'none';
}

function setupEventListeners() {
    const filterPlant = document.getElementById('filter-plant');
    if (filterPlant) {
        filterPlant.addEventListener('change', () => {
            const pVal = filterPlant.value;
            const filtered = (pVal === 'all') 
                ? allSessions 
                : allSessions.filter(s => s.plant_id === Number(pVal));
            renderGallery(filtered);
        });
    }

    const closeBtn = document.getElementById('modal-close');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    const modal = document.getElementById('gallery-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    }
}
