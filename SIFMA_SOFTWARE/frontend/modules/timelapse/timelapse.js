// SIFMA — Controlador Modular: Time-Lapse Evolutivo
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let frames = [];
let currentIndex = 0;
let isPlaying = false;
let playInterval = null;
let playSpeed = 500;
let growthChart = null;

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Time-Lapse & Evolución Biológica';
    if (subheading) subheading.textContent = 'Visor cronológico y reproducción secuencial de desarrollo vegetativo para Canastilla #1';

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

    const slider = document.getElementById('timeline-slider');
    if (slider) slider.value = currentIndex;

    setText('player-frame-counter', `Fotograma ${currentIndex + 1} / ${frames.length}`);
    setText('hud-date-text', current.date);
    setText('hud-period-text', `Día ${current.day} / ${frames.length}`);
    setText('time-foliar-area', `${current.foliar_area.toFixed(2)} cm²`);
    setText('time-height', `${current.plant_height.toFixed(2)} cm`);

    drawFrameCanvas(currentIndex);

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

    // Fondo
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, w, h);

    // Tubo PVC
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(w / 2 - 35, h - 90, 70, 90);

    // Crecimiento progresivo
    const progress = (index + 1) / frames.length;
    const stemHeight = 50 + progress * 170;

    ctx.strokeStyle = '#15803d';
    ctx.lineWidth = 4 + progress * 4;
    ctx.beginPath();
    ctx.moveTo(w / 2, h - 90);
    ctx.lineTo(w / 2, h - 90 - stemHeight);
    ctx.stroke();

    // Hojas
    const leafSpread = 35 + progress * 95;
    drawBlade(ctx, w / 2, h - 90 - stemHeight * 0.7, -40, leafSpread * 0.9);
    drawBlade(ctx, w / 2, h - 90 - stemHeight * 0.8, 35, leafSpread * 0.85);
    if (progress > 0.3) {
        drawBlade(ctx, w / 2, h - 90 - stemHeight * 0.9, -20, leafSpread * 0.95);
        drawBlade(ctx, w / 2, h - 90 - stemHeight, 15, leafSpread);
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
                borderColor: '#059669',
                backgroundColor: 'rgba(5, 150, 105, 0.1)',
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
        setText('play-icon', 'play_arrow');
        setText('play-text', 'Reproducir');
    } else {
        isPlaying = true;
        setText('play-icon', 'pause');
        setText('play-text', 'Pausar');
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
            btn.classList.add('active');
            playSpeed = Number(btn.dataset.speed);
            if (isPlaying) {
                togglePlay();
                togglePlay();
            }
        });
    });
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.textContent = val;
}
