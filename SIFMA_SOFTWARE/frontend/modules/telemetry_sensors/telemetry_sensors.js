// SIFMA — Controlador Modular: Telemetría de Sensores
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let telemetryChart = null;
let pollTimer = null;

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Análisis y Telemetría Detallada de Sensores';
    if (subheading) subheading.textContent = 'Monitoreo ambiental en vivo, recepción inalámbrica XBee y registro continuo';

    await updateLiveTelemetry();
    await renderHistoryChart('all');
    setupEventListeners();

    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(updateLiveTelemetry, 3000);
}

async function updateLiveTelemetry() {
    try {
        const data = await TauriBridge.invoke('get_live_telemetry');
        if (!data) return;

        setText('kpi-ph-val', data.ph.toFixed(2));
        setText('kpi-ec-val', data.ec);
        setText('kpi-turb-val', data.turbidity.toFixed(2));
        setText('kpi-do-val', data.dissolved_oxygen.toFixed(2));
        setText('kpi-wtemp-val', data.water_temp.toFixed(2));
        setText('kpi-tank-val', data.tank_level_pct.toFixed(1));
        setText('kpi-atemp-val', data.air_temp.toFixed(1));
        setText('kpi-ahum-val', `${data.humidity.toFixed(1)}%`);
    } catch (err) {
        console.error('[TELEMETRY SENSORS ERROR]', err);
    }
}

async function renderHistoryChart(filter) {
    const ctx = document.getElementById('telemetryHistoryChart');
    if (!ctx) return;

    try {
        const history = await TauriBridge.invoke('get_sensor_history', { hours: 24 }) || [];
        if (!history.length) return;

        if (telemetryChart) telemetryChart.destroy();

        const labels = history.map(h => h.timestamp);
        const datasets = [];

        if (filter === 'all' || filter === 'water') {
            datasets.push({
                label: 'pH Solución (x10)',
                data: history.map(h => (h.ph * 10).toFixed(1)),
                borderColor: '#ec4899',
                borderWidth: 2,
                tension: 0.35,
                pointRadius: 2
            });
            datasets.push({
                label: 'EC (µS/cm)',
                data: history.map(h => h.ec),
                borderColor: '#8b5cf6',
                borderWidth: 2,
                tension: 0.35,
                pointRadius: 2
            });
        }

        if (filter === 'all' || filter === 'temps') {
            datasets.push({
                label: 'Temp. Solución (°C)',
                data: history.map(h => h.water_temp),
                borderColor: '#059669',
                backgroundColor: 'rgba(5, 150, 105, 0.08)',
                borderWidth: 2,
                tension: 0.35,
                pointRadius: 2
            });
            datasets.push({
                label: 'Temp. Ambiente (°C)',
                data: history.map(h => h.air_temp),
                borderColor: '#2563eb',
                borderWidth: 2,
                tension: 0.35,
                pointRadius: 2
            });
        }

        telemetryChart = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { boxWidth: 12, font: { family: 'Literata', size: 11 } }
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
    const reconnectBtn = document.getElementById('btn-reconnect-serial');
    if (reconnectBtn) {
        reconnectBtn.addEventListener('click', async () => {
            const port = document.getElementById('antenna-port-select')?.value || 'COM3';
            reconnectBtn.disabled = true;
            reconnectBtn.textContent = 'Conectando...';
            try {
                await TauriBridge.invoke('connect_serial_port', { port, baud_rate: 115200 });
                setText('antenna-live-status-text', `Transmitiendo en Vivo (${port})`);
            } finally {
                reconnectBtn.disabled = false;
                reconnectBtn.innerHTML = '<span class="material-icons-round" style="font-size: 14px;">refresh</span><span>Reconectar</span>';
            }
        });
    }

    const btnAll = document.getElementById('btn-chart-all');
    const btnWater = document.getElementById('btn-chart-water');
    const btnTemps = document.getElementById('btn-chart-temps');

    [btnAll, btnWater, btnTemps].forEach(btn => {
        if (!btn) return;
        btn.addEventListener('click', () => {
            [btnAll, btnWater, btnTemps].forEach(b => b?.classList.remove('active'));
            btn.classList.add('active');
            if (btn === btnAll) renderHistoryChart('all');
            else if (btn === btnWater) renderHistoryChart('water');
            else if (btn === btnTemps) renderHistoryChart('temps');
        });
    });
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.textContent = val;
}
