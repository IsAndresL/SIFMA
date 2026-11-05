// SIFMA — Controlador Modular: Dossier Científico
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

export async function initModule() {
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = 'Generación de Dossier Técnico y Científico';

    await loadDossierData();
    setupEventListeners();
}

async function loadDossierData() {
    try {
        const dossier = await TauriBridge.invoke('get_scientific_dossier', { plant_id: 1 });
        if (!dossier) return;

        const speciesEl = document.getElementById('dossier-species');
        if (speciesEl) speciesEl.textContent = dossier.species;

        const cycleEl = document.getElementById('dossier-cycle');
        if (cycleEl) cycleEl.textContent = dossier.cycle_code;
    } catch (err) {
        console.error('[DOSSIER ERROR]', err);
    }
}

function setupEventListeners() {
    const printBtn = document.getElementById('btn-print-pdf');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }

    const csvBtn = document.getElementById('btn-export-csv');
    if (csvBtn) {
        csvBtn.addEventListener('click', () => {
            const csvRows = [
                ['SIFMA - Registro Fenotipico y Microclimatico'],
                ['Codigo Ensayo', 'CICLO-2026-A1'],
                ['Especie', 'Allium fistulosum'],
                ['Fecha Exportacion', new Date().toISOString()],
                [],
                ['Dia', 'Planta_ID', 'Area_Foliar_cm2', 'Altura_cm', 'Temp_Agua_C', 'Temp_Aire_C', 'pH', 'EC_uS_cm'],
                ['1', '1', '24.0', '8.0', '24.1', '27.8', '6.2', '1240'],
                ['2', '1', '25.4', '8.9', '24.3', '28.1', '6.1', '1255'],
                ['3', '1', '27.1', '9.8', '24.0', '27.9', '6.2', '1235'],
                ['4', '1', '28.8', '10.7', '24.2', '28.4', '6.3', '1260'],
                ['5', '1', '30.5', '11.6', '24.5', '28.5', '6.2', '1248']
            ];

            const csvContent = 'data:text/csv;charset=utf-8,' + csvRows.map(e => e.join(',')).join('\n');
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', 'SIFMA_Dossier_Datos_2026.csv');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }
}
