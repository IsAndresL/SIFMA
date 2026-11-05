// SIFMA — Controlador Modular: Cruce Multivariable
import { TauriBridge } from '../../core/scripts/tauri_bridge.js';

let scatterChartInstance = null;

export async function initModule() {
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) pageTitle.textContent = 'Análisis de Correlación Bivariable y Multivariada';

    await loadCrossAnalysis();
    await loadCorrelationMatrix();
    setupEventListeners();
}

async function loadCrossAnalysis() {
    try {
        const varX = document.getElementById('select-var-x')?.value || 'water_temp';
        const varY = document.getElementById('select-var-y')?.value || 'foliar_area';

        const data = await TauriBridge.invoke('get_cross_analysis_data', { var_x: varX, var_y: varY });
        if (!data) return;

        // Actualizar badges e indicadores
        setText('badge-pearson-r', `r = ${data.pearson_r.toFixed(3)}`);
        setText('badge-r2', `R² = ${data.r_squared.toFixed(3)}`);
        setText('stat-r', data.pearson_r.toFixed(3));
        setText('stat-r2', data.r_squared.toFixed(3));
        setText('stat-slope', `+${data.slope.toFixed(2)} / unidad`);
        setText('stat-intercept', `${data.intercept.toFixed(1)}`);
        setText('stat-p', `< ${data.p_value}`);
        setText('stat-n', `${data.points.length} puntos`);
        setText('interp-text', data.interpretation);

        renderScatterChart(data);
    } catch (err) {
        console.error('[CROSS ANALYSIS ERROR]', err);
    }
}

function renderScatterChart(data) {
    const ctx = document.getElementById('crossScatterChart');
    if (!ctx) return;

    if (scatterChartInstance) {
        scatterChartInstance.destroy();
    }

    const scatterPoints = data.points.map(p => ({ x: p.x, y: p.y }));

    // Calcular línea de regresión de mínimos cuadrados
    const minX = Math.min(...data.points.map(p => p.x));
    const maxX = Math.max(...data.points.map(p => p.x));
    const linePoints = [
        { x: minX, y: minX * data.slope + data.intercept },
        { x: maxX, y: maxX * data.slope + data.intercept }
    ];

    scatterChartInstance = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Observaciones Experimentales',
                    data: scatterPoints,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    pointRadius: 5
                },
                {
                    label: 'Línea de Regresión OLS',
                    data: linePoints,
                    type: 'line',
                    borderColor: '#6366f1',
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
                legend: { position: 'top', labels: { font: { family: 'Inter', size: 11 } } }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Variable Independiente (X)', font: { size: 11 } },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: { font: { family: 'JetBrains Mono', size: 10 } }
                },
                y: {
                    title: { display: true, text: 'Variable Dependiente (Y)', font: { size: 11 } },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: { font: { family: 'JetBrains Mono', size: 10 } }
                }
            }
        }
    });
}

async function loadCorrelationMatrix() {
    try {
        const matrixData = await TauriBridge.invoke('get_correlation_matrix');
        const table = document.getElementById('correlation-matrix-table');
        if (!table || !matrixData) return;

        let html = '<thead><tr><th>Variables</th>';
        matrixData.labels.forEach(l => { html += `<th>${l}</th>`; });
        html += '</tr></thead><tbody>';

        matrixData.matrix.forEach((row, rIdx) => {
            html += `<tr><th>${matrixData.labels[rIdx]}</th>`;
            row.forEach((val) => {
                let cls = 'cell-neutral';
                if (val >= 0.7) cls = 'cell-pos-high';
                else if (val >= 0.3) cls = 'cell-pos-med';
                else if (val <= -0.6) cls = 'cell-neg-high';
                else if (val <= -0.3) cls = 'cell-neg-med';

                html += `<td class="${cls}">${val.toFixed(2)}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody>';
        table.innerHTML = html;
    } catch (err) {
        console.error('[CORRELATION MATRIX ERROR]', err);
    }
}

function setupEventListeners() {
    const btn = document.getElementById('btn-recalc');
    if (btn) btn.addEventListener('click', loadCrossAnalysis);

    const selX = document.getElementById('select-var-x');
    const selY = document.getElementById('select-var-y');
    if (selX) selX.addEventListener('change', loadCrossAnalysis);
    if (selY) selY.addEventListener('change', loadCrossAnalysis);
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}
