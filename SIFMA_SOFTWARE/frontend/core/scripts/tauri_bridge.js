// SIFMA — Puente IPC Desacoplado para Tauri 2.0
// Proporciona invocación tipada hacia el backend en Rust con modo simulación seguro.

export const TauriBridge = {
    isTauriAvailable() {
        return typeof window !== 'undefined' && 
               window.__TAURI__ !== undefined && 
               window.__TAURI__.core !== undefined;
    },

    async invoke(cmd, args = {}) {
        if (this.isTauriAvailable()) {
            try {
                return await window.__TAURI__.core.invoke(cmd, args);
            } catch (err) {
                console.error(`[TAURI IPC ERROR] ${cmd}:`, err);
                throw err;
            }
        } else {
            return this.mockResponse(cmd, args);
        }
    },

    mockResponse(cmd, args) {
        switch (cmd) {
            case 'get_system_info':
                return {
                    app_version: '2.0.0-desktop',
                    rust_version: '1.99.1',
                    platform: 'windows-x86_64',
                    database_status: 'online',
                    python_sidecar_status: 'ready',
                    database_path: 'local_server/sifma.db',
                    serial_port: 'COM3 (115200 baud)'
                };

            case 'get_dashboard_summary':
                return {
                    plant_id: args.plant_id || 1,
                    crop_name: 'Cebollín (Allium fistulosum)',
                    water_temp: 24.2,
                    air_temp: 28.5,
                    humidity: 64.0,
                    foliar_area: 61.8,
                    plant_height: 18.5,
                    stem_diameter: 4.8,
                    health_index: 82.8,
                    ph: 6.2,
                    ec: 1250.0,
                    dissolved_oxygen: 7.4,
                    turbidity: 2.1,
                    pump_status: 'ACTIVE'
                };

            case 'get_live_telemetry':
                return {
                    water_temp: +(23.8 + Math.random() * 0.8).toFixed(1),
                    air_temp: +(27.9 + Math.random() * 1.2).toFixed(1),
                    humidity: +(63 + Math.random() * 4).toFixed(1),
                    ph: +(6.1 + Math.random() * 0.3).toFixed(2),
                    ec: Math.round(1220 + Math.random() * 50),
                    dissolved_oxygen: +(7.2 + Math.random() * 0.4).toFixed(1),
                    turbidity: +(1.9 + Math.random() * 0.5).toFixed(1),
                    tank_level_pct: 88.5,
                    pump_active: true,
                    timestamp: new Date().toISOString()
                };

            case 'get_sensor_history': {
                const hours = args.hours || 24;
                const points = [];
                const now = Date.now();
                for (let i = hours; i >= 0; i--) {
                    const t = new Date(now - i * 3600 * 1000);
                    points.push({
                        timestamp: t.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
                        water_temp: +(23.5 + Math.sin(i / 3) * 1.5 + Math.random() * 0.3).toFixed(1),
                        air_temp: +(27.0 + Math.sin(i / 2.5) * 2.5 + Math.random() * 0.4).toFixed(1),
                        humidity: +(62.0 + Math.cos(i / 4) * 8.0 + Math.random() * 1.0).toFixed(1),
                        ph: +(6.2 + Math.sin(i / 5) * 0.2).toFixed(2),
                        ec: Math.round(1240 + Math.sin(i / 4) * 40)
                    });
                }
                return points;
            }

            case 'list_serial_ports':
                return ['COM1 (Estándar)', 'COM3 (Arduino Mega / SIFMA Telemetría)', 'COM4 (FTDI Serial)'];

            case 'connect_serial_port':
                return { success: true, port: args.port || 'COM3', baud_rate: args.baud_rate || 115200 };

            case 'get_cross_analysis_data':
                return {
                    pearson_r: 0.842,
                    r_squared: 0.709,
                    slope: 1.84,
                    intercept: 12.1,
                    p_value: 0.0004,
                    interpretation: 'Correlación fuertemente positiva estadísticamente significativa (p < 0.001). Un incremento térmico dentro del rango óptimo (22-26°C) estimula el área foliar a razón de 1.84 cm²/°C.',
                    points: Array.from({ length: 25 }, (_, i) => ({
                        x: +(22 + i * 0.3 + Math.random() * 0.5).toFixed(1),
                        y: +(50 + i * 0.9 + Math.random() * 2.5).toFixed(1),
                        plant_id: (i % 12) + 1,
                        date: `2026-11-${String((i % 5) + 1).padStart(2, '0')}`
                    }))
                };

            case 'get_correlation_matrix':
                return {
                    labels: ['T. Agua', 'T. Aire', 'Humedad', 'pH', 'EC', 'Área Foliar', 'Altura'],
                    matrix: [
                        [1.00, 0.72, -0.45, 0.12, 0.28, 0.84, 0.79],
                        [0.72, 1.00, -0.68, 0.08, 0.19, 0.65, 0.71],
                        [-0.45, -0.68, 1.00, -0.15, -0.10, -0.32, -0.28],
                        [0.12, 0.08, -0.15, 1.00, 0.35, 0.18, 0.14],
                        [0.28, 0.19, -0.10, 0.35, 1.00, 0.54, 0.49],
                        [0.84, 0.65, -0.32, 0.18, 0.54, 1.00, 0.92],
                        [0.79, 0.71, -0.28, 0.14, 0.49, 0.92, 1.00]
                    ]
                };

            case 'list_capture_sessions':
                return [
                    { id: 101, plant_id: 1, timestamp: '2026-11-04 14:30', foliar_area: 61.8, plant_height: 18.5, stem_diameter: 4.8, health_index: 82.8, status: 'PROCESADO' },
                    { id: 100, plant_id: 2, timestamp: '2026-11-04 14:15', foliar_area: 58.2, plant_height: 17.2, stem_diameter: 4.5, health_index: 85.1, status: 'PROCESADO' },
                    { id: 99, plant_id: 3, timestamp: '2026-11-04 14:00', foliar_area: 64.9, plant_height: 19.1, stem_diameter: 5.1, health_index: 80.4, status: 'PROCESADO' },
                    { id: 98, plant_id: 1, timestamp: '2026-11-03 14:30', foliar_area: 59.4, plant_height: 17.9, stem_diameter: 4.6, health_index: 81.9, status: 'PROCESADO' },
                    { id: 97, plant_id: 2, timestamp: '2026-11-03 14:15', foliar_area: 56.1, plant_height: 16.8, stem_diameter: 4.3, health_index: 84.7, status: 'PROCESADO' }
                ];

            case 'trigger_vision_processing':
                return {
                    status: 'success',
                    session_id: Date.now(),
                    foliar_area: +(58 + Math.random() * 8).toFixed(1),
                    plant_height: +(17 + Math.random() * 3).toFixed(1),
                    stem_diameter: +(4.2 + Math.random() * 1.0).toFixed(1),
                    health_index: +(80 + Math.random() * 10).toFixed(1),
                    green_coverage_pct: +(35.4 + Math.random() * 5).toFixed(1),
                    chlorophyll_index_exg: +(0.42 + Math.random() * 0.08).toFixed(3),
                    processing_time_ms: 184
                };

            case 'get_timelapse_frames':
                return Array.from({ length: 12 }, (_, i) => ({
                    day: i + 1,
                    date: `2026-10-${String(20 + i).padStart(2, '0')}`,
                    foliar_area: +(24.0 + i * 3.4 + Math.sin(i) * 0.8).toFixed(1),
                    plant_height: +(8.0 + i * 0.95).toFixed(1),
                    image_url: 'core/assets/sifma_sin_texto.svg'
                }));

            case 'get_scientific_dossier':
                return {
                    title: 'Dossier Científico y Fenotípico de Torre Hidropónica SIFMA',
                    cycle_code: 'CICLO-2026-A1',
                    species: 'Allium fistulosum (Cebollín de Rama)',
                    total_plants: 12,
                    total_days: 28,
                    observations_count: 336,
                    mean_growth_rate: '1.42 cm²/día',
                    r_temperature_foliar: 0.842,
                    water_use_efficiency: '96.4%',
                    dnda_deposit_code: 'SIFMA-DOC-ARQ-2026',
                    verified_by: 'Administrador SIFMA / Agrónomo en Jefe'
                };

            case 'get_crop_profiles':
                return [
                    { id: 1, name: 'Cebollín (Allium fistulosum)', temp_min: 18.0, temp_opt: 24.0, temp_max: 30.0, ph_min: 6.0, ph_max: 6.8, ec_min: 1000, ec_max: 1500, cycle_days: 60, active: true },
                    { id: 2, name: 'Albahaca (Ocimum basilicum)', temp_min: 20.0, temp_opt: 25.0, temp_max: 32.0, ph_min: 5.8, ph_max: 6.5, ec_min: 1200, ec_max: 1800, cycle_days: 45, active: false },
                    { id: 3, name: 'Lechuga Romana (Lactuca sativa)', temp_min: 15.0, temp_opt: 21.0, temp_max: 26.0, ph_min: 5.6, ph_max: 6.4, ec_min: 900, ec_max: 1400, cycle_days: 40, active: false },
                    { id: 4, name: 'Menta Piperita (Mentha piperita)', temp_min: 16.0, temp_opt: 22.0, temp_max: 28.0, ph_min: 6.0, ph_max: 7.0, ec_min: 1100, ec_max: 1600, cycle_days: 50, active: false }
                ];

            case 'get_audit_logs':
                return [
                    { id: 1, timestamp: '2026-11-05 00:01:12', user: 'admin', event_type: 'AUTH_SUCCESS', ip: '127.0.0.1', resource: '/login', status: 'OK', hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' },
                    { id: 2, timestamp: '2026-11-04 23:45:00', user: 'system', event_type: 'TELEMETRY_INGEST', ip: 'COM3', resource: '/serial', status: 'OK', hash: '5b992e34b3d1521ac9ac66465720fcf4f8b2556532f5ec1391699b612864213d' },
                    { id: 3, timestamp: '2026-11-04 22:30:15', user: 'admin', event_type: 'PROFILE_UPDATE', ip: '127.0.0.1', resource: '/crop/1', status: 'OK', hash: 'b14a7b8059d9f0e7932372d59291f4961a2cf9e05f82bda63a44e53b62d01305' },
                    { id: 4, timestamp: '2026-11-04 18:20:41', user: 'system', event_type: 'VISION_BATCH', ip: 'sidecar-ipc', resource: '/vision/101', status: 'OK', hash: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069' }
                ];

            case 'get_users_list':
                return [
                    { id: 1, username: 'admin', role: 'ADMINISTRADOR', full_name: 'Administrador SIFMA', active: true, created_at: '2026-10-01' },
                    { id: 2, username: 'agronomo', role: 'INVESTIGADOR', full_name: 'Ing. Carlos Mendoza', active: true, created_at: '2026-10-05' },
                    { id: 3, username: 'tecnico', role: 'OPERADOR', full_name: 'Laura Gómez', active: true, created_at: '2026-10-12' }
                ];

            default:
                return { status: 'mock_ok', cmd, args };
        }
    }
};
