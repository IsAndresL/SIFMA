/* ==========================================================================
   SIFMA - DETAILED ENVIRONMENTAL SENSORS GRAPHICS (FASE 2)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof sensorRaw !== 'undefined' && sensorRaw.length > 0) {
        const labels = sensorRaw.map(s => s.time);
        const tempData = sensorRaw.map(s => s.temp);
        const humData = sensorRaw.map(s => s.hum);
        const uvData = sensorRaw.map(s => s.uv);
        const currData = sensorRaw.map(s => s.curr);

        // Helper to create an elegant, responsive line chart with custom styling
        const createSensorChart = (ctxId, label, data, borderColor, glowColor, suffix) => {
            const ctx = document.getElementById(ctxId);
            if (!ctx) return;

            // Generate premium linear gradient under the line
            const canvasContext = ctx.getContext('2d');
            const grad = canvasContext.createLinearGradient(0, 0, 0, 250);
            grad.addColorStop(0, glowColor);
            grad.addColorStop(1, 'rgba(0,0,0,0)');

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: label,
                        data: data,
                        borderColor: borderColor,
                        borderWidth: 2.5,
                        backgroundColor: grad,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: borderColor,
                        pointBorderColor: '#ffffff',
                        pointHoverRadius: 7,
                        pointHoverBackgroundColor: borderColor,
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#0f172a',
                            titleColor: '#ffffff',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(255,255,255,0.08)',
                            borderWidth: 1,
                            padding: 12,
                            cornerRadius: 10,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    return ` ${context.dataset.label}: ${context.parsed.y}${suffix}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(15, 23, 42, 0.05)' },
                            ticks: { color: '#475569', font: { family: 'Inter', size: 11 } }
                        },
                        y: {
                            grid: { color: 'rgba(15, 23, 42, 0.05)' },
                            ticks: { 
                                color: '#475569', 
                                font: { family: 'Inter', size: 11 },
                                callback: value => `${value}${suffix}`
                            }
                        }
                    }
                }
            });
        };

        // Initialize each detailed chart with premium colors
        // Red glow for Temperature
        createSensorChart('tempChart', 'Temperatura', tempData, '#ef4444', 'rgba(239, 68, 68, 0.2)', '°C');
        
        // Blue glow for Humidity
        createSensorChart('humidityChart', 'Humedad Relativa', humData, '#3b82f6', 'rgba(59, 130, 246, 0.2)', '%');
        
        // Amber/Golden glow for UV Radiation
        createSensorChart('uvChart', 'Radiación UV', uvData, '#f59e0b', 'rgba(245, 158, 11, 0.2)', ' lux');
        
        // Emerald/Mint glow for Pump Current
        createSensorChart('currentChart', 'Corriente Bomba', currData, '#10b981', 'rgba(16, 185, 129, 0.2)', ' A');
    }
});
