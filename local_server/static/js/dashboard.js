/* ==========================================================================
   SIFMA - FRONTEND INTERACTIVE CHARTS AND CLIENT LOGIC
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. CONFIGURACIÓN DEL GRÁFICO DE CRECIMIENTO BIOMÉTRICO
    const ctxGrowth = document.getElementById('growthChart');
    if (ctxGrowth && typeof growthData !== 'undefined') {
        
        // Preparar vectores de datos
        const labels = growthData.map(d => {
            // Formatear fecha simple: de YYYY-MM-DD a DD/MM
            const parts = d.date.split('-');
            return parts.length === 3 ? `${parts[2]}/${parts[1]}` : d.date;
        });
        
        const areaData = growthData.map(d => d.area);
        const heightData = growthData.map(d => d.height);
        const diameterData = growthData.map(d => d.diameter);
        
        // Crear gradiente verde para área foliar
        const gradGreen = ctxGrowth.getContext('2d').createLinearGradient(0, 0, 0, 300);
        gradGreen.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
        gradGreen.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
        
        // Crear gradiente azul para altura
        const gradBlue = ctxGrowth.getContext('2d').createLinearGradient(0, 0, 0, 300);
        gradBlue.addColorStop(0, 'rgba(59, 130, 246, 0.2)');
        gradBlue.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

        new Chart(ctxGrowth, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Área Foliar (cm²)',
                        data: areaData,
                        borderColor: '#10b981',
                        borderWidth: 3,
                        backgroundColor: gradGreen,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#ffffff',
                        pointHoverRadius: 8,
                        yAxisID: 'yArea'
                    },
                    {
                        label: 'Altura Planta (cm)',
                        data: heightData,
                        borderColor: '#3b82f6',
                        borderWidth: 2.5,
                        backgroundColor: gradBlue,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#3b82f6',
                        pointBorderColor: '#ffffff',
                        pointHoverRadius: 6,
                        yAxisID: 'yHeight'
                    },
                    {
                        label: 'Diámetro Tallo (mm)',
                        data: diameterData,
                        borderColor: '#f59e0b',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.35,
                        pointBackgroundColor: '#f59e0b',
                        pointBorderColor: '#ffffff',
                        pointHoverRadius: 6,
                        yAxisID: 'yHeight' // Comparte el eje Y derecho
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#94a3b8',
                            font: { family: 'Inter', size: 12, weight: '500' },
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#ffffff',
                        bodyColor: '#e2e8f0',
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        usePointStyle: true
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(15, 23, 42, 0.04)' },
                        ticks: { color: '#475569', font: { family: 'Inter' } }
                    },
                    yArea: {
                        type: 'linear',
                        position: 'left',
                        beginAtZero: true,
                        grid: { color: 'rgba(15, 23, 42, 0.05)' },
                        ticks: { 
                            color: '#10b981', 
                            font: { family: 'Inter', weight: '600' },
                            callback: function(value) {
                                const cleanVal = Math.floor(value) === value ? value : parseFloat(value.toFixed(2));
                                return `${cleanVal} cm²`;
                            }
                        },
                        title: { display: true, text: 'Área Foliar (cm²)', color: '#10b981' }
                    },
                    yHeight: {
                        type: 'linear',
                        position: 'right',
                        beginAtZero: true,
                        grid: { drawOnChartArea: false }, // Evita superposición de líneas cuadrículas
                        ticks: { 
                            color: '#475569', 
                            font: { family: 'Inter' },
                            callback: function(value) {
                                return Math.floor(value) === value ? value : parseFloat(value.toFixed(2));
                            }
                        },
                        title: { display: true, text: 'Altura (cm) / Espesor (mm)', color: '#475569' }
                    }
                }
            }
        });
    }

    // 2. CONFIGURACIÓN DEL GRÁFICO DE TELEMETRÍA RESUMIDA (CLIMATOLOGÍA)
    const ctxSummary = document.getElementById('sensorSummaryChart');
    if (ctxSummary && typeof sensorRaw !== 'undefined' && sensorRaw.length > 0) {
        const labels = sensorRaw.map(s => s.time);
        const tempData = sensorRaw.map(s => s.temp);
        const humData = sensorRaw.map(s => s.hum);

        // Green/Blue gradient for Temperature and Humidity overlays
        const gradRed = ctxSummary.getContext('2d').createLinearGradient(0, 0, 0, 300);
        gradRed.addColorStop(0, 'rgba(239, 68, 68, 0.15)');
        gradRed.addColorStop(1, 'rgba(239, 68, 68, 0.0)');

        const gradBlue = ctxSummary.getContext('2d').createLinearGradient(0, 0, 0, 300);
        gradBlue.addColorStop(0, 'rgba(59, 130, 246, 0.15)');
        gradBlue.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

        new Chart(ctxSummary, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Temperatura (°C)',
                        data: tempData,
                        borderColor: '#ef4444',
                        borderWidth: 2.5,
                        backgroundColor: gradRed,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#ef4444',
                        pointBorderColor: '#ffffff',
                        pointHoverRadius: 7,
                        yAxisID: 'yTemp'
                    },
                    {
                        label: 'Humedad Relativa (%)',
                        data: humData,
                        borderColor: '#3b82f6',
                        borderWidth: 2.5,
                        backgroundColor: gradBlue,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#3b82f6',
                        pointBorderColor: '#ffffff',
                        pointHoverRadius: 7,
                        yAxisID: 'yHum'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#94a3b8',
                            font: { family: 'Inter', size: 12, weight: '500' },
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#ffffff',
                        bodyColor: '#e2e8f0',
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        usePointStyle: true
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(15, 23, 42, 0.04)' },
                        ticks: { color: '#475569', font: { family: 'Inter' } }
                    },
                    yTemp: {
                        type: 'linear',
                        position: 'left',
                        grid: { color: 'rgba(15, 23, 42, 0.05)' },
                        ticks: { 
                            color: '#ef4444', 
                            font: { family: 'Inter', weight: '600' },
                            callback: value => `${value} °C`
                        },
                        title: { display: true, text: 'Temperatura', color: '#ef4444' }
                    },
                    yHum: {
                        type: 'linear',
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { 
                            color: '#3b82f6', 
                            font: { family: 'Inter', weight: '600' },
                            callback: value => `${value} %`
                        },
                        title: { display: true, text: 'Humedad Relativa', color: '#3b82f6' }
                    }
                }
            }
        });
    }
});
