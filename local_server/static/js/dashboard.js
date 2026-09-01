/**
 * SIFMA - LÓGICA DE GRÁFICAS DEL DASHBOARD ANALÍTICO DIARIO
 * Renderizado de las 4 gráficas del día seleccionado usando Chart.js
 */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof dailyData === 'undefined') return;

    // Configuración global de fuentes para Chart.js
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = '#64748b';

    // 1. GRÁFICA 1: CURVA TÉRMICA DE LA JORNADA
    const ctxThermal = document.getElementById('thermalCurveChart');
    if (ctxThermal) {
        const thermal = dailyData.thermal_curve || {};
        const labels = thermal.labels || ["07:00", "10:00", "13:00", "16:00", "19:00"];
        const temps = thermal.temps || [0, 0, 0, 0, 0];

        const gradientTemp = ctxThermal.getContext('2d').createLinearGradient(0, 0, 0, 200);
        gradientTemp.addColorStop(0, 'rgba(239, 68, 68, 0.25)');
        gradientTemp.addColorStop(1, 'rgba(37, 99, 235, 0.02)');

        new Chart(ctxThermal, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Temperatura (°C)',
                        data: temps,
                        borderColor: '#2563eb',
                        backgroundColor: gradientTemp,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#1d4ed8',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#09211a',
                        titleColor: '#ffffff',
                        bodyColor: '#e2e8f0',
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => ` Temperatura: ${ctx.parsed.y} °C`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    },
                    y: {
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            callback: (v) => `${v}°C`,
                            font: { size: 11 }
                        },
                        beginAtZero: true,
                        suggestedMax: Math.max(...temps, 30)
                    }
                }
            }
        });
    }

    // 2. GRÁFICA 2: CRECIMIENTO Y MORFOMETRÍA POR PERÍODO
    const ctxGrowth = document.getElementById('growthPeriodsChart');
    if (ctxGrowth) {
        const growth = dailyData.growth_chart || {};
        const labels = growth.labels || ["Mañana", "Mediodía", "Tarde"];
        const areas = growth.areas || [0, 0, 0];

        const gradientBars = ctxGrowth.getContext('2d').createLinearGradient(0, 0, 0, 200);
        gradientBars.addColorStop(0, '#059669');
        gradientBars.addColorStop(1, '#10b981');

        new Chart(ctxGrowth, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Área Foliar (cm²)',
                    data: areas,
                    backgroundColor: gradientBars,
                    borderRadius: 8,
                    barThickness: 36
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#09211a',
                        titleColor: '#ffffff',
                        bodyColor: '#e2e8f0',
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => ` Área Foliar: ${ctx.parsed.y} cm²`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 12, weight: 600 } }
                    },
                    y: {
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            callback: (v) => `${v} cm²`,
                            font: { size: 11 }
                        },
                        beginAtZero: true,
                        suggestedMax: Math.max(...areas, 50)
                    }
                }
            }
        });
    }

    // 3. GRÁFICA 3: CORRIENTE DE BOMBA (AMPERAJE)
    const ctxPump = document.getElementById('pumpCurrentChart');
    if (ctxPump) {
        const pump = dailyData.pump_chart || {};
        const labels = pump.labels || ["07:00", "10:00", "13:00", "16:00", "19:00"];
        const currents = pump.currents || [0, 0, 0, 0, 0];

        const gradientPump = ctxPump.getContext('2d').createLinearGradient(0, 0, 0, 200);
        gradientPump.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
        gradientPump.addColorStop(1, 'rgba(16, 185, 129, 0.02)');

        new Chart(ctxPump, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Corriente Motor (A)',
                    data: currents,
                    borderColor: '#059669',
                    backgroundColor: gradientPump,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#047857',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#09211a',
                        titleColor: '#ffffff',
                        bodyColor: '#e2e8f0',
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => ` Corriente: ${ctx.parsed.y} A`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    },
                    y: {
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            callback: (v) => `${v} A`,
                            font: { size: 11 }
                        },
                        beginAtZero: true,
                        suggestedMax: Math.max(...currents, 0.6)
                    }
                }
            }
        });
    }

    // 4. GRÁFICA 4: RADIACIÓN SOLAR UV (LUX)
    const ctxSolar = document.getElementById('solarIrradianceChart');
    if (ctxSolar) {
        const solar = dailyData.solar_chart || {};
        const labels = solar.labels || ["07:00", "09:00", "11:00", "13:00", "15:00", "17:00", "19:00"];
        const uvs = solar.uv_values || [0, 0, 0, 0, 0, 0, 0];

        new Chart(ctxSolar, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Radiación (lux)',
                    data: uvs,
                    backgroundColor: '#f59e0b',
                    borderRadius: 6,
                    barThickness: 24
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#09211a',
                        titleColor: '#ffffff',
                        bodyColor: '#e2e8f0',
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => ` Radiación: ${ctx.parsed.y} lux`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    },
                    y: {
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            callback: (v) => `${v} lux`,
                            font: { size: 11 }
                        },
                        beginAtZero: true,
                        suggestedMax: Math.max(...uvs, 600)
                    }
                }
            }
        });
    }
});
