// SIFMA — Controlador Modular: Procesamiento de Visión
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let currentStage = 'rgb';

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Pipeline de Visión Artificial y Segmentación';
    if (subheading) subheading.textContent = 'Procesamiento de capturas USB / archivos ZIP por fecha y canastilla hidropónica';

    drawCanvasStage(currentStage);
    await loadSessionsTable();
    setupEventListeners();
}

function drawCanvasStage(stage) {
    const canvas = document.getElementById('visionPreviewCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (stage === 'rgb') {
        // Fondo base
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, w, h);

        // Tubo de cultivo PVC
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(w / 2 - 35, h - 110, 70, 110);
        ctx.strokeStyle = '#cbd5e1';
        ctx.strokeRect(w / 2 - 35, h - 110, 70, 110);

        // Tallo Cebollín
        ctx.strokeStyle = '#15803d';
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(w / 2, h - 110);
        ctx.lineTo(w / 2, h - 230);
        ctx.stroke();

        // Hojas verdes
        ctx.fillStyle = '#16a34a';
        drawBlade(ctx, w / 2, h - 230, -45, 110);
        drawBlade(ctx, w / 2, h - 200, 45, 100);
        drawBlade(ctx, w / 2, h - 180, -30, 95);
        drawBlade(ctx, w / 2, h - 220, 15, 120);

    } else if (stage === 'exg') {
        ctx.fillStyle = '#0b0f19';
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(w / 2, h - 110);
        ctx.lineTo(w / 2, h - 230);
        ctx.stroke();

        ctx.fillStyle = '#e2e8f0';
        drawBlade(ctx, w / 2, h - 230, -45, 110);
        drawBlade(ctx, w / 2, h - 200, 45, 100);
        drawBlade(ctx, w / 2, h - 180, -30, 95);
        drawBlade(ctx, w / 2, h - 220, 15, 120);

    } else if (stage === 'otsu') {
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(w / 2, h - 110);
        ctx.lineTo(w / 2, h - 230);
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        drawBlade(ctx, w / 2, h - 230, -45, 110);
        drawBlade(ctx, w / 2, h - 200, 45, 100);
        drawBlade(ctx, w / 2, h - 180, -30, 95);
        drawBlade(ctx, w / 2, h - 220, 15, 120);

    } else if (stage === 'contour') {
        drawCanvasStage('rgb');

        // Bounding box
        ctx.strokeStyle = '#0284c7';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(w / 2 - 75, h - 340, 160, 230);
        ctx.setLineDash([]);

        // Calibre altura
        ctx.strokeStyle = '#d97706';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(w / 2 - 90, h - 340);
        ctx.lineTo(w / 2 - 90, h - 110);
        ctx.stroke();

        ctx.fillStyle = '#d97706';
        ctx.font = '11px JetBrains Mono';
        ctx.fillText('H = 18.5 cm', w / 2 - 155, h - 220);

        // Calibre tallo
        ctx.strokeStyle = '#ec4899';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(w / 2 - 15, h - 115);
        ctx.lineTo(w / 2 + 15, h - 115);
        ctx.stroke();

        ctx.fillStyle = '#ec4899';
        ctx.fillText('Ø = 4.8 mm', w / 2 + 25, h - 112);
    }
}

function drawBlade(ctx, startX, startY, angleDeg, length) {
    const rad = (angleDeg - 90) * (Math.PI / 180);
    const endX = startX + Math.cos(rad) * length;
    const endY = startY + Math.sin(rad) * length;

    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.quadraticCurveTo(startX + (endX - startX) * 0.5 + 15, startY + (endY - startY) * 0.5, endX, endY);
    ctx.quadraticCurveTo(startX + (endX - startX) * 0.5 - 15, startY + (endY - startY) * 0.5, startX, startY);
    ctx.fill();
}

async function loadSessionsTable() {
    try {
        const sessions = await TauriBridge.invoke('list_capture_sessions');
        const tbody = document.getElementById('proc-sessions-tbody');
        if (!tbody || !sessions) return;

        let html = '';
        sessions.forEach(s => {
            html += `
                <tr>
                    <td><code>#${s.id}</code></td>
                    <td style="font-family: var(--font-mono); font-size: 12px;">${s.timestamp}</td>
                    <td><strong style="color: var(--accent-success);">${s.foliar_area} cm²</strong></td>
                    <td>${s.plant_height} cm</td>
                    <td>${s.stem_diameter} mm</td>
                    <td><span class="badge badge-success">${s.health_index}%</span></td>
                    <td><span class="badge badge-primary">${s.status}</span></td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('[LOAD SESSIONS ERROR]', err);
    }
}

function setupEventListeners() {
    document.querySelectorAll('.filter-btn[data-step]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn[data-step]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentStage = btn.dataset.step;
            setText('stage-badge-indicator', `Etapa: ${btn.textContent}`);
            drawCanvasStage(currentStage);
        });
    });

    const procBtn = document.getElementById('btn-process-sidecar');
    if (procBtn) {
        procBtn.addEventListener('click', async () => {
            procBtn.disabled = true;
            procBtn.innerHTML = '<span class="material-icons-round">autorenew</span><span>Invocando Sidecar...</span>';
            try {
                const res = await TauriBridge.invoke('trigger_vision_processing', {
                    image_path: 'captures/plant_01.jpg',
                    crop_id: 1
                });
                if (res) {
                    setText('p-area', `${res.foliar_area.toFixed(2)} cm²`);
                    setText('p-height', `${res.plant_height.toFixed(2)} cm`);
                    setText('p-stem', `${res.stem_diameter.toFixed(2)} mm`);
                    setText('p-health', `${res.health_index.toFixed(2)} %`);
                    setText('p-latency', `${res.processing_time_ms} ms`);
                    document.querySelector('.filter-btn[data-step="contour"]')?.click();
                }
            } finally {
                procBtn.disabled = false;
                procBtn.innerHTML = '<span class="material-icons-round">play_arrow</span><span>Ejecutar Pipeline Sidecar</span>';
            }
        });
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.textContent = val;
}
