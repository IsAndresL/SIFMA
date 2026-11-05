// SIFMA — Controlador del Módulo Dashboard
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let chartInstance = null;

export async function initModule() {
    console.log('[DASHBOARD] Inicializando componente reactivo...');
    
    try {
        const data = await TauriBridge.invoke('get_dashboard_summary', { plant_id: 1 });
        updateKpiValues(data);
        renderMicroclimateChart();
    } catch (err) {
        console.error('[DASHBOARD ERROR] Fallo al cargar datos de telemetría:', err);
    }
}

function updateKpiValues(data) {
    if (!data) return;
    
    document.getElementById('kpi-area').textContent = `${data.foliar_area ?? 61.8} cm²`;
    document.getElementById('kpi-height').textContent = `${data.plant_height ?? 18.5} cm`;
    document.getElementById('kpi-stem').textContent = `${data.stem_diameter ?? 4.8} mm`;
    document.getElementById('kpi-health').textContent = `${data.health_index ?? 82.8} %`;

    document.getElementById('val-ph').textContent = (data.ph ?? 6.2).toFixed(1);
    document.getElementById('val-ec').textContent = `${(data.ec ?? 1250).toFixed(0)} µS/cm`;
    document.getElementById('val-do').textContent = `${(data.dissolved_oxygen ?? 7.4).toFixed(1)} mg/L`;
    document.getElementById('val-turb').textContent = `${(data.turbidity ?? 2.1).toFixed(1)} NTU`;
}

function renderMicroclimateChart() {
    const canvas = document.getElementById('chart-microclimate');
    if (!canvas) return;

    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }

    const hours = ['06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00'];
    const tempData = [23.1, 24.5, 27.2, 29.8, 30.1, 28.4, 25.6];
    const solarData = [800, 4200, 18500, 38000, 36500, 14200, 1200];

    chartInstance = new Chart(canvas, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [
                {
                    label: 'Temperatura Aire (°C)',
                    data: tempData,
                    borderColor: '#e11d48',
                    backgroundColor: 'rgba(225, 29, 72, 0.08)',
                    yAxisID: 'yTemp',
                    tension: 0.35,
                    fill: true
                },
                {
                    label: 'Radiación Solar (lux)',
                    data: solarData,
                    borderColor: '#d97706',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    yAxisID: 'ySolar',
                    tension: 0.35
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                yTemp: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Temperatura (°C)' }
                },
                ySolar: {
                    type: 'linear',
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    title: { display: true, text: 'Radiación (lux)' }
                }
            }
        }
    });
}
