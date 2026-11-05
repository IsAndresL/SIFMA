// SIFMA — Comandos IPC: Dashboard Ejecutivo y KPIs
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct DashboardSummary {
    pub plant_id: i32,
    pub crop_name: String,
    pub water_temp: f64,
    pub air_temp: f64,
    pub humidity: f64,
    pub foliar_area: f64,
    pub plant_height: f64,
    pub stem_diameter: f64,
    pub health_index: f64,
    pub ph: f64,
    pub ec: f64,
    pub dissolved_oxygen: f64,
    pub turbidity: f64,
    pub pump_status: String,
}

#[tauri::command]
pub fn get_dashboard_summary(plant_id: Option<i32>) -> DashboardSummary {
    let pid = plant_id.unwrap_or(1);
    DashboardSummary {
        plant_id: pid,
        crop_name: "Cebollín (Allium fistulosum)".to_string(),
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
        pump_status: "ACTIVE".to_string(),
    }
}

