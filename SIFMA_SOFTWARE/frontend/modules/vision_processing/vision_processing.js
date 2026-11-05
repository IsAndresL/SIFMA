// SIFMA — Controlador Modular: Procesamiento de Visión
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let currentStep = 'rgb';

export async function initModule() {
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = 'Procesamiento de Fenotipado y Extracción Biométrica';

    drawCanvasStage(currentStep);
    await loadRecentSessions();
    setupEventListeners();
}

function drawCanvasStage(step) {
    const canvas = document.getElementById('visionPreviewCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (step === 'rgb') {
        // Fondo simulado torre hidropónica
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, w, h);

        // Tubo de PVC blanco
        ctx.fillStyle = '#f1f5f9';
        ctx.fillRect(w / 2 - 40, h - 140, 80, 140);
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 2;
        ctx.strokeRect(w / 2 - 40, h - 140, 80, 140);

        // Tallo y Hojas verdes de cebollín
        ctx.strokeStyle = '#15803d';
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(w / 2, h - 140);
        ctx.lineTo(w / 2, h - 260);
        ctx.stroke();

        // Hojas
        ctx.fillStyle = '#22c55e';
        drawLeaf(ctx, w / 2, h - 260, -45, 120);
        drawLeaf(ctx, w / 2, h - 230, 45, 110);
        drawLeaf(ctx, w / 2, h - 200, -35, 100);
        drawLeaf(ctx, w / 2, h - 240, 10, 130);

    } else if (step === 'exg') {
        // ExG Grayscale representation
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(w / 2, h - 140);
        ctx.lineTo(w / 2, h - 260);
        ctx.stroke();

        ctx.fillStyle = '#e2e8f0';
        drawLeaf(ctx, w / 2, h - 260, -45, 120);
        drawLeaf(ctx, w / 2, h - 230, 45, 110);
        drawLeaf(ctx, w / 2, h - 200, -35, 100);
        drawLeaf(ctx, w / 2, h - 240, 10, 130);

    } else if (step === 'otsu') {
        // Pure binary mask (Otsu thresholding)
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(w / 2, h - 140);
        ctx.lineTo(w / 2, h - 260);
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        drawLeaf(ctx, w / 2, h - 260, -45, 120);
        drawLeaf(ctx, w / 2, h - 230, 45, 110);
        drawLeaf(ctx, w / 2, h - 200, -35, 100);
        drawLeaf(ctx, w / 2, h - 240, 10, 130);

    } else if (step === 'contour') {
        // Contornos verdes + Calibración métrica y caja envolvente
        drawCanvasStage('rgb');

        // Bounding box foliar
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(w / 2 - 80, h - 390, 170, 260);
        ctx.setLineDash([]);

        // Indicador de altura
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(w / 2 - 95, h - 390);
        ctx.lineTo(w / 2 - 95, h - 140);
        ctx.stroke();

        // Texto de medición
        ctx.fillStyle = '#f59e0b';
        ctx.font = '11px JetBrains Mono';
        ctx.fillText('H = 18.5 cm', w / 2 - 165, h - 260);

        // Indicador de diámetro basal
        ctx.strokeStyle = '#ec4899';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(w / 2 - 15, h - 145);
        ctx.lineTo(w / 2 + 15, h - 145);
        ctx.stroke();
        ctx.fillStyle = '#ec4899';
        ctx.fillText('Ø = 4.8 mm', w / 2 + 25, h - 142);
    }
}

function drawLeaf(ctx, startX, startY, angleDeg, length) {
    const rad = (angleDeg - 90) * (Math.PI / 180);
    const endX = startX + Math.cos(rad) * length;
    const endY = startY + Math.sin(rad) * length;

    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.quadraticCurveTo(startX + (endX - startX) * 0.5 + 20, startY + (endY - startY) * 0.5, endX, endY);
    ctx.quadraticCurveTo(startX + (endX - startX) * 0.5 - 20, startY + (endY - startY) * 0.5, startX, startY);
    ctx.fill();
}

async function loadRecentSessions() {
    try {
        const sessions = await TauriBridge.invoke('list_capture_sessions');
        const tbody = document.getElementById('vision-sessions-tbody');
        if (!tbody || !sessions) return;

        let html = '';
        sessions.forEach(s => {
            html += `
                <tr>
                    <td class="font-mono">#${s.id}</td>
                    <td>Planta #${s.plant_id}</td>
                    <td class="font-mono">${s.timestamp}</td>
                    <td class="font-mono">${s.foliar_area}</td>
                    <td class="font-mono">${s.plant_height}</td>
                    <td class="font-mono">${s.stem_diameter}</td>
                    <td class="font-mono text-emerald">${s.health_index}%</td>
                    <td><span class="badge badge-emerald">${s.status}</span></td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('[SESSIONS ERROR]', err);
    }
}

function setupEventListeners() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentStep = e.target.dataset.step;
            const badge = document.getElementById('stage-badge');
            if (badge) badge.textContent = `Etapa: ${e.target.textContent}`;
            drawCanvasStage(currentStep);
        });
    });

    const runBtn = document.getElementById('btn-run-vision');
    if (runBtn) {
        runBtn.addEventListener('click', async () => {
            runBtn.disabled = true;
            runBtn.textContent = 'Procesando en Python...';
            try {
                const res = await TauriBridge.invoke('trigger_vision_processing', {
                    image_path: 'captures/plant_01.jpg',
                    crop_id: 1
                });
                if (res) {
                    document.getElementById('bio-foliar-area').textContent = res.foliar_area;
                    document.getElementById('bio-plant-height').textContent = res.plant_height;
                    document.getElementById('bio-stem-diameter').textContent = res.stem_diameter;
                    document.getElementById('bio-coverage').textContent = res.green_coverage_pct;
                    document.getElementById('bio-health').textContent = res.health_index;
                    document.getElementById('bio-latency').textContent = res.processing_time_ms;

                    // Cambiar a vista de contornos
                    document.querySelector('.tab-btn[data-step="contour"]')?.click();
                }
            } catch (err) {
                console.error(err);
            } finally {
                runBtn.disabled = false;
                runBtn.textContent = 'Procesar en Sidecar';
            }
        });
    }
}
