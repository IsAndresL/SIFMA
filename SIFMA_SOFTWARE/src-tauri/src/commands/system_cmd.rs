// SIFMA — Comandos IPC: Información y Diagnóstico del Sistema
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct SystemInfoResponse {
    pub app_version: String,
    pub rust_version: String,
    pub platform: String,
    pub database_status: String,
    pub python_sidecar_status: String,
}

#[tauri::command]
pub fn get_system_info() -> SystemInfoResponse {
    SystemInfoResponse {
        app_version: "2.0.0".to_string(),
        rust_version: "1.99.1".to_string(),
        platform: std::env::consts::OS.to_string(),
        database_status: "online".to_string(),
        python_sidecar_status: "standby".to_string(),
    }
}
