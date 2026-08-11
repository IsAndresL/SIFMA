/* ==========================================================================
   SIFMA - DETAILED PLANT BIOMETRICS CHARTS (IMAGE ANALYSIS)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof growthData !== 'undefined' && growthData.length > 0) {
        
        // Prepare datasets
        const labels = growthData.map(d => {
            const parts = d.date.split('-');
            return parts.length === 3 ? `${parts[2]}/${parts[1]}` : d.date;
        });

        const areaData = growthData.map(d => d.area);
        const heightData = growthData.map(d => d.height);
        const diameterData = growthData.map(d => d.diameter);
        const healthData = growthData.map(d => d.health);

        // Helper to instantiate premium dark-slate scale line charts
        const createBiometricChart = (ctxId, label, data, borderColor, glowColor, suffix, maxVal = null) => {
            const ctx = document.getElementById(ctxId);
            if (!ctx) return;

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
                            grid: { color: 'rgba(15, 23, 42, 0.04)' },
                            ticks: { color: '#475569', font: { family: 'Inter', size: 11 } }
                        },
                        y: {
                            beginAtZero: true,
                            max: maxVal,
                            grid: { color: 'rgba(15, 23, 42, 0.05)' },
                            ticks: { 
                                color: '#475569', 
                                font: { family: 'Inter', size: 11 },
                                callback: function(value) {
                                    const cleanVal = Math.floor(value) === value ? value : parseFloat(value.toFixed(2));
                                    return `${cleanVal}${suffix}`;
                                }
                            }
                        }
                    }
                }
            });
        };

        // Initialize each detailed biometric chart with premium colors
        // Foliar Area (Emerald green)
        createBiometricChart('foliarAreaChart', 'Área Foliar', areaData, '#10b981', 'rgba(16, 185, 129, 0.2)', ' cm²');

        // Plant Height (Electric blue)
        createBiometricChart('plantHeightChart', 'Altura Planta', heightData, '#3b82f6', 'rgba(59, 130, 246, 0.2)', ' cm');

        // Stem Diameter (Amber orange)
        createBiometricChart('stemDiameterChart', 'Diámetro Tallo', diameterData, '#f59e0b', 'rgba(245, 158, 11, 0.2)', ' mm');

        // Health Index (Vibrant Red)
        createBiometricChart('healthIndexChart', 'Índice de Salud', healthData, '#dc2626', 'rgba(220, 38, 38, 0.15)', '%', 100);
    }
});
