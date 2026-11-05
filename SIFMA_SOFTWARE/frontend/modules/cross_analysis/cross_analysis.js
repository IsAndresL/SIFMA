// SIFMA — Controlador Modular: Cruce Multivariable
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let scatterChart = null;

export async function initModule() {
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');
    if (heading) heading.textContent = 'Cruce de Datos y Análisis Multivariable';
    if (subheading) subheading.textContent = 'Sincronización cronológica, matriz de correlación de Pearson y laboratorio gráfico para Canastilla #1';

    await loadHeatmapMatrix();
    await loadRegressionData();
}

async function loadHeatmapMatrix() {
    try {
        const matrixData = await TauriBridge.invoke('get_correlation_matrix');
        const table = document.getElementById('heatmap-correlation-table');
        if (!table || !matrixData) return;

        let html = '<thead><tr><th>Variable Ambiental \\ Fenotipo</th>';
        matrixData.labels.forEach(l => { html += `<th>${l}</th>`; });
        html += '</tr></thead><tbody>';

        matrixData.matrix.forEach((row, rIdx) => {
            html += `<tr><td style="font-weight: 700; background: #f8fafc;">${matrixData.labels[rIdx]}</td>`;
            row.forEach((val) => {
                let bg = 'rgba(255, 255, 255, 1)';
                let color = 'var(--text-body)';
                let fontW = '500';

                if (val >= 0.7) {
                    bg = 'rgba(5, 150, 105, 0.2)';
                    color = '#047857';
                    fontW = '700';
                } else if (val >= 0.3) {
                    bg = 'rgba(5, 150, 105, 0.08)';
                    color = '#059669';
                } else if (val <= -0.6) {
                    bg = 'rgba(220, 38, 38, 0.18)';
                    color = '#b91c1c';
                    fontW = '700';
                } else if (val <= -0.3) {
                    bg = 'rgba(220, 38, 38, 0.08)';
                    color = '#dc2626';
                }

                html += `
                    <td style="background: ${bg}; color: ${color}; font-weight: ${fontW}; text-align: center; cursor: pointer;" title="r = ${val.toFixed(2)}">
                        <span style="font-family: var(--font-mono); font-size: 12px;">${val > 0 ? '+' : ''}${val.toFixed(2)}</span>
                    </td>
                `;
            });
            html += '</tr>';
        });
        html += '</tbody>';
        table.innerHTML = html;
    } catch (err) {
        console.error('[HEATMAP ERROR]', err);
    }
}

async function loadRegressionData() {
    try {
        const data = await TauriBridge.invoke('get_cross_analysis_data', { var_x: 'water_temp', var_y: 'foliar_area' });
        if (!data) return;

        setText('cross-badge-r', `r = +${data.pearson_r.toFixed(3)}`);
        setText('cross-badge-r2', `R² = ${data.r_squared.toFixed(3)}`);
        setText('c-stat-r', `+${data.pearson_r.toFixed(3)}`);
        setText('c-stat-r2', data.r_squared.toFixed(3));
        setText('c-stat-slope', `+${data.slope.toFixed(2)} cm²/°C`);
        setText('c-stat-p', `< ${data.p_value}`);
        setText('cross-interp-text', data.interpretation);

        renderScatterChart(data);
    } catch (err) {
        console.error('[REGRESSION ERROR]', err);
    }
}

function renderScatterChart(data) {
    const ctx = document.getElementById('crossScatterChart');
    if (!ctx) return;

    if (scatterChart) scatterChart.destroy();

    const scatterPoints = data.points.map(p => ({ x: p.x, y: p.y }));
    const minX = Math.min(...data.points.map(p => p.x));
    const maxX = Math.max(...data.points.map(p => p.x));
    const linePoints = [
        { x: minX, y: minX * data.slope + data.intercept },
        { x: maxX, y: maxX * data.slope + data.intercept }
    ];

    scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Observaciones Experimentales',
                    data: scatterPoints,
                    backgroundColor: 'rgba(5, 150, 105, 0.75)',
                    borderColor: '#059669',
                    pointRadius: 5
                },
                {
                    label: 'Ajuste Lineal OLS',
                    data: linePoints,
                    type: 'line',
                    borderColor: '#2563eb',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { font: { family: 'Literata', size: 11 } } }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Temperatura Solución Nutritiva (°C)', font: { size: 11 } },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: { font: { family: 'JetBrains Mono', size: 10 } }
                },
                y: {
                    title: { display: true, text: 'Área Foliar (cm²)', font: { size: 11 } },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: { font: { family: 'JetBrains Mono', size: 10 } }
                }
            }
        }
    });
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.textContent = val;
}
