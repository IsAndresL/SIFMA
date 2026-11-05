// SIFMA — Núcleo Nativo de Escritorio (Tauri 2.0)
// Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
// Año: 2026.

pub mod domain;
pub mod infrastructure;
pub mod application;
pub mod commands;

use infrastructure::db::{DbConnection, initialize_schema, seed_initial_data};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 1. Inicializar base de datos SQLite en disco local
    let db_path = "sifma_desktop.db";
    if let Ok(conn) = DbConnection::open(db_path) {
        let _ = initialize_schema(&conn);
        let _ = seed_initial_data(&conn);
        println!("[SIFMA DESKTOP] Base de datos SQLite inicializada exitosamente en modo WAL.");
    }

    // 2. Arrancar runtime de Tauri con comandos registrados
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            commands::get_system_info,
            commands::get_dashboard_summary,
            commands::login_user,
            commands::get_live_telemetry,
            commands::get_sensor_history,
            commands::list_serial_ports,
            commands::connect_serial_port,
            commands::get_cross_analysis_data,
            commands::get_correlation_matrix,
            commands::list_capture_sessions,
            commands::trigger_vision_processing,
            commands::get_timelapse_frames,
            commands::get_scientific_dossier,
            commands::get_crop_profiles,
            commands::get_audit_logs,
            commands::get_users_list,
        ])
        .run(tauri::generate_context!())
        .expect("Error al ejecutar la aplicación SIFMA Desktop");
}
