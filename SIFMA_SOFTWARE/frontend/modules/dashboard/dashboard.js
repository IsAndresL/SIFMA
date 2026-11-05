// SIFMA — Controlador Modular: Dashboard Analítico
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let chartThermal = null;
let chartGrowth = null;
let chartHumidity = null;
let chartPumping = null;

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Dashboard Analítico';
    if (subheading) subheading.textContent = 'Resumen general de la jornada: 2026-11-05';

    await loadDashboardSummary();
    renderAllCharts();
}

async function loadDashboardSummary() {
    try {
        const plantId = Number(document.getElementById('header-plant-selector')?.value || 1);
        const data = await TauriBridge.invoke('get_dashboard_summary', { plant_id: plantId });
        if (!data) return;

        setText('dash-foliar-area', data.foliar_area.toFixed(2));
        setText('dash-temp', data.water_temp.toFixed(2));
        setText('dash-humidity', data.humidity.toFixed(2));
        setText('dash-health', data.health_index.toFixed(2));
        setText('dash-height', `${data.plant_height.toFixed(1)} cm`);
    } catch (err) {
        console.error('[DASHBOARD ERROR]', err);
    }
}

function renderAllCharts() {
    // 1. Curva Térmica Diaria (thermalCurveChart)
    const ctxThermal = document.getElementById('thermalCurveChart');
    if (ctxThermal) {
        if (chartThermal) chartThermal.destroy();
        chartThermal = new Chart(ctxThermal, {
            type: 'line',
            data: {
                labels: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
                datasets: [
                    {
                        label: 'Temp. Solución (°C)',
                        data: [23.1, 22.8, 22.4, 23.9, 25.8, 26.4, 25.1, 24.0],
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.08)',
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3
                    },
                    {
                        label: 'Temp. Ambiente (°C)',
                        data: [24.5, 23.9, 23.2, 26.5, 29.8, 30.2, 27.5, 25.8],
                        borderColor: '#2563eb',
                        borderDash: [4, 4],
                        fill: false,
                        tension: 0.35,
                        pointRadius: 2
                    }
                ]
            },
            options: getChartOptions('Temperatura (°C)')
        });
    }

    // 2. Dinámica de Crecimiento Foliar (growthCurveChart)
    const ctxGrowth = document.getElementById('growthCurveChart');
    if (ctxGrowth) {
        if (chartGrowth) chartGrowth.destroy();
        chartGrowth = new Chart(ctxGrowth, {
            type: 'bar',
            data: {
                labels: ['Día 1', 'Día 4', 'Día 8', 'Día 12', 'Día 16', 'Día 20', 'Día 24', 'Día 28'],
                datasets: [{
                    label: 'Área Foliar (cm²)',
                    data: [24.0, 28.5, 34.2, 41.0, 48.6, 54.2, 59.8, 61.8],
                    backgroundColor: 'rgba(5, 150, 105, 0.75)',
                    borderRadius: 4
                }]
            },
            options: getChartOptions('Área (cm²)')
        });
    }

    // 3. Humedad y Radiación Solar (humidityChart)
    const ctxHum = document.getElementById('humidityChart');
    if (ctxHum) {
        if (chartHumidity) chartHumidity.destroy();
        chartHumidity = new Chart(ctxHum, {
            type: 'line',
            data: {
                labels: ['06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00'],
                datasets: [
                    {
                        label: 'Humedad Relativa (%)',
                        data: [78, 72, 65, 58, 62, 68, 74],
                        borderColor: '#0284c7',
                        yAxisID: 'y',
                        tension: 0.35
                    },
                    {
                        label: 'Radiación (x1000 lux)',
                        data: [5, 12, 22, 28, 25, 14, 4],
                        borderColor: '#d97706',
                        yAxisID: 'y1',
                        borderDash: [3, 3],
                        tension: 0.35
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { family: 'Literata', size: 11 } } } },
                scales: {
                    x: { grid: { color: 'rgba(0,0,0,0.04)' } },
                    y: { type: 'linear', position: 'left', grid: { color: 'rgba(0,0,0,0.04)' } },
                    y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false } }
                }
            }
        });
    }

    // 4. Eficiencia de Bombeo y Balance Nutricional (pumpingChart)
    const ctxPump = document.getElementById('pumpingChart');
    if (ctxPump) {
        if (chartPumping) chartPumping.destroy();
        chartPumping = new Chart(ctxPump, {
            type: 'line',
            data: {
                labels: ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8'],
                datasets: [
                    {
                        label: 'EC (µS/cm)',
                        data: [1230, 1240, 1255, 1245, 1260, 1250, 1248, 1250],
                        borderColor: '#7c3aed',
                        tension: 0.3,
                        pointRadius: 3
                    },
                    {
                        label: 'pH (x200)',
                        data: [1240, 1242, 1244, 1240, 1246, 1244, 1245, 1244],
                        borderColor: '#0d9488',
                        tension: 0.3,
                        pointRadius: 3
                    }
                ]
            },
            options: getChartOptions('Parámetros Nutritivos')
        });
    }
}

function getChartOptions(yTitle) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: { boxWidth: 10, font: { family: 'Literata', size: 11 } }
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(0,0,0,0.04)' },
                ticks: { font: { family: 'JetBrains Mono', size: 10 } }
            },
            y: {
                title: { display: true, text: yTitle, font: { size: 10 } },
                grid: { color: 'rgba(0,0,0,0.04)' },
                ticks: { font: { family: 'JetBrains Mono', size: 10 } }
            }
        }
    };
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.textContent = val;
}
