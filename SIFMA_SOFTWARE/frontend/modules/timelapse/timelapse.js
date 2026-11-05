// SIFMA — Controlador Modular: Time-Lapse Evolutivo
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let frames = [];
let currentIndex = 0;
let isPlaying = false;
let playInterval = null;
let playSpeed = 500;
let growthChart = null;

export async function initModule() {
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = 'Time-Lapse y Cinética Evolutiva del Cultivo';

    await loadFrames();
    setupEventListeners();
}

async function loadFrames() {
    try {
        frames = await TauriBridge.invoke('get_timelapse_frames', { plant_id: 1 }) || [];
        if (!frames.length) return;

        initGrowthChart();
        updateFrame(0);
    } catch (err) {
        console.error('[TIMELAPSE ERROR]', err);
    }
}

function updateFrame(index) {
    if (!frames.length || index < 0 || index >= frames.length) return;
    currentIndex = index;
    const current = frames[currentIndex];

    // Actualizar sliders y etiquetas
    const slider = document.getElementById('timeline-slider');
    if (slider) slider.value = currentIndex;

    const dayBadge = document.getElementById('player-day-badge');
    if (dayBadge) dayBadge.textContent = `Día ${current.day} / ${frames.length}`;

    const dateBadge = document.getElementById('player-date-badge');
    if (dateBadge) dateBadge.textContent = current.date;

    const areaEl = document.getElementById('time-foliar-area');
    if (areaEl) areaEl.textContent = `${current.foliar_area} cm²`;

    const heightEl = document.getElementById('time-height');
    if (heightEl) heightEl.textContent = `${current.plant_height} cm`;

    // Renderizar canvas interactivo con morfología proporcional al día
    drawFrameCanvas(currentIndex);

    // Actualizar punto activo en el gráfico
    if (growthChart) {
        growthChart.setActiveElements([{ datasetIndex: 0, index: currentIndex }]);
        growthChart.update();
    }
}

function drawFrameCanvas(index) {
    const canvas = document.getElementById('timelapseCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    // Fondo oscuro de cámara de fenotipado
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, w, h);

    // Base del tubo hidropónico
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(w / 2 - 40, h - 100, 80, 100);

    // Crecimiento progresivo de cebollín
    const progress = (index + 1) / frames.length; // 0.08 a 1.0
    const stemHeight = 60 + progress * 160;

    ctx.strokeStyle = '#15803d';
    ctx.lineWidth = 4 + progress * 4;
    ctx.beginPath();
    ctx.moveTo(w / 2, h - 100);
    ctx.lineTo(w / 2, h - 100 - stemHeight);
    ctx.stroke();

    // Hojas que brotan y se ensanchan
    ctx.fillStyle = '#22c55e';
    const leafSpread = 40 + progress * 90;

    drawBlade(ctx, w / 2, h - 100 - stemHeight * 0.7, -40, leafSpread * 0.9);
    drawBlade(ctx, w / 2, h - 100 - stemHeight * 0.8, 35, leafSpread * 0.85);
    if (progress > 0.3) {
        drawBlade(ctx, w / 2, h - 100 - stemHeight * 0.9, -20, leafSpread * 0.95);
        drawBlade(ctx, w / 2, h - 100 - stemHeight, 15, leafSpread);
    }
}

function drawBlade(ctx, startX, startY, angleDeg, length) {
    const rad = (angleDeg - 90) * (Math.PI / 180);
    const endX = startX + Math.cos(rad) * length;
    const endY = startY + Math.sin(rad) * length;

    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.lineWidth = 4;
    ctx.strokeStyle = '#22c55e';
    ctx.stroke();
}

function initGrowthChart() {
    const ctx = document.getElementById('timelapseGrowthChart');
    if (!ctx) return;

    if (growthChart) growthChart.destroy();

    growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: frames.map(f => `D${f.day}`),
            datasets: [{
                label: 'Área (cm²)',
                data: frames.map(f => f.foliar_area),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { font: { family: 'JetBrains Mono', size: 9 } } },
                y: { ticks: { font: { family: 'JetBrains Mono', size: 9 } } }
            }
        }
    });
}

function togglePlay() {
    if (isPlaying) {
        clearInterval(playInterval);
        isPlaying = false;
        document.getElementById('play-icon').textContent = 'play_arrow';
        document.getElementById('play-text').textContent = 'Reproducir';
    } else {
        isPlaying = true;
        document.getElementById('play-icon').textContent = 'pause';
        document.getElementById('play-text').textContent = 'Pausar';
        playInterval = setInterval(() => {
            let next = currentIndex + 1;
            if (next >= frames.length) next = 0;
            updateFrame(next);
        }, playSpeed);
    }
}

function setupEventListeners() {
    const playBtn = document.getElementById('btn-play-pause');
    if (playBtn) playBtn.addEventListener('click', togglePlay);

    const resetBtn = document.getElementById('btn-reset-timeline');
    if (resetBtn) resetBtn.addEventListener('click', () => {
        if (isPlaying) togglePlay();
        updateFrame(0);
    });

    const slider = document.getElementById('timeline-slider');
    if (slider) {
        slider.addEventListener('input', (e) => {
            if (isPlaying) togglePlay();
            updateFrame(Number(e.target.value));
        });
    }

    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            playSpeed = Number(e.target.dataset.speed);
            if (isPlaying) {
                togglePlay();
                togglePlay();
            }
        });
    });
}
