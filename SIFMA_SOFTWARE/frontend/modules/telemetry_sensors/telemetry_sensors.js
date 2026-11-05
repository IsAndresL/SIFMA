// SIFMA — Controlador Modular: Telemetría de Sensores
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let telemetryChartInstance = null;
let telemetryInterval = null;

export async function initModule() {
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = 'Monitoreo de Telemetría Microclimática en Tiempo Real';

    await updateLiveTelemetry();
    await renderTelemetryChart('all');
    setupEventListeners();

    if (telemetryInterval) clearInterval(telemetryInterval);
    telemetryInterval = setInterval(updateLiveTelemetry, 3000);
}

async function updateLiveTelemetry() {
    try {
        const data = await TauriBridge.invoke('get_live_telemetry');
        if (!data) return;

        setText('val-water-temp', data.water_temp);
        setText('val-air-temp', data.air_temp);
        setText('val-humidity', data.humidity);
        setText('val-ph', data.ph);
        setText('val-ec', data.ec);
        setText('val-do', data.dissolved_oxygen);

        const tankEl = document.getElementById('val-tank-level');
        if (tankEl) {
            tankEl.textContent = `Tanque: ${data.tank_level_pct}% | Bomba: ${data.pump_active ? 'Activa' : 'Inactiva'}`;
        }
    } catch (err) {
        console.error('[TELEMETRY] Error al obtener telemetría:', err);
    }
}

async function renderTelemetryChart(filter) {
    const ctx = document.getElementById('telemetryHistoryChart');
    if (!ctx) return;

    try {
        const history = await TauriBridge.invoke('get_sensor_history', { hours: 24 });
        if (!history || !history.length) return;

        const labels = history.map(h => h.timestamp);

        if (telemetryChartInstance) {
            telemetryChartInstance.destroy();
        }

        const datasets = [];

        if (filter === 'all' || filter === 'temp') {
            datasets.push({
                label: 'Temp. Solución (°C)',
                data: history.map(h => h.water_temp),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                tension: 0.35,
                pointRadius: 2
            });
            datasets.push({
                label: 'Temp. Ambiente (°C)',
                data: history.map(h => h.air_temp),
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                borderWidth: 2,
                tension: 0.35,
                pointRadius: 2
            });
        }

        if (filter === 'all' || filter === 'ph_ec') {
            datasets.push({
                label: 'pH Solución (x10)',
                data: history.map(h => (h.ph * 10).toFixed(1)),
                borderColor: '#6366f1',
                borderWidth: 2,
                tension: 0.35,
                pointRadius: 2
            });
            datasets.push({
                label: 'Humedad (%)',
                data: history.map(h => h.humidity),
                borderColor: '#0284c7',
                borderWidth: 2,
                tension: 0.35,
                pointRadius: 2
            });
        }

        telemetryChartInstance = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { boxWidth: 12, font: { family: 'Inter', size: 11 } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(0,0,0,0.04)' },
                        ticks: { font: { family: 'JetBrains Mono', size: 10 } }
                    },
                    y: {
                        grid: { color: 'rgba(0,0,0,0.04)' },
                        ticks: { font: { family: 'JetBrains Mono', size: 10 } }
                    }
                }
            }
        });
    } catch (err) {
        console.error('[CHART ERROR]', err);
    }
}

function setupEventListeners() {
    document.querySelectorAll('.btn-filter').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderTelemetryChart(e.target.dataset.metric);
        });
    });

    const toggleBtn = document.getElementById('btn-toggle-serial');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', async () => {
            const port = document.getElementById('serial-port-select')?.value || 'COM3';
            toggleBtn.disabled = true;
            toggleBtn.textContent = 'Conectando...';
            try {
                await TauriBridge.invoke('connect_serial_port', { port, baud_rate: 115200 });
                document.getElementById('serial-status-text').textContent = `Conectado a ${port} @ 115200 baud — OK`;
            } catch (err) {
                console.error('Error serial:', err);
            } finally {
                toggleBtn.disabled = false;
                toggleBtn.textContent = 'Reconectar';
            }
        });
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.textContent = val;
}
