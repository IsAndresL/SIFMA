// SIFMA — Comandos IPC: Telemetría y Conexión Serial
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone)]
pub struct LiveTelemetryDTO {
    pub water_temp: f64,
    pub air_temp: f64,
    pub humidity: f64,
    pub ph: f64,
    pub ec: i32,
    pub dissolved_oxygen: f64,
    pub turbidity: f64,
    pub tank_level_pct: f64,
    pub pump_active: bool,
    pub timestamp: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct SensorHistoryDTO {
    pub timestamp: String,
    pub water_temp: f64,
    pub air_temp: f64,
    pub humidity: f64,
    pub ph: f64,
    pub ec: i32,
}

#[derive(Serialize, Deserialize)]
pub struct SerialConnectResult {
    pub success: bool,
    pub port: String,
    pub baud_rate: u32,
}

#[tauri::command]
pub fn get_live_telemetry() -> LiveTelemetryDTO {
    LiveTelemetryDTO {
        water_temp: 24.2,
        air_temp: 28.5,
        humidity: 64.0,
        ph: 6.22,
        ec: 1250,
        dissolved_oxygen: 7.4,
        turbidity: 2.1,
        tank_level_pct: 88.5,
        pump_active: true,
        timestamp: "2026-11-05T00:00:00Z".to_string(),
    }
}

#[tauri::command]
pub fn get_sensor_history(hours: Option<i32>) -> Vec<SensorHistoryDTO> {
    let count = hours.unwrap_or(24);
    let mut history = Vec::new();
    for i in (0..=count).rev() {
        let hour_str = format!("{:02}:00", (24 - i).rem_euclid(24));
        history.push(SensorHistoryDTO {
            timestamp: hour_str,
            water_temp: 23.5 + ((i as f64) * 0.1),
            air_temp: 27.0 + ((i as f64) * 0.15),
            humidity: 62.0 + ((i as f64) * 0.2),
            ph: 6.20,
            ec: 1240,
        });
    }
    history
}

#[tauri::command]
pub fn list_serial_ports() -> Vec<String> {
    vec![
        "COM1 (Estándar)".to_string(),
        "COM3 (Arduino Mega / SIFMA Telemetría)".to_string(),
        "COM4 (FTDI Serial)".to_string(),
    ]
}

#[tauri::command]
pub fn connect_serial_port(port: String, baud_rate: u32) -> SerialConnectResult {
    SerialConnectResult {
        success: true,
        port,
        baud_rate,
    }
}
