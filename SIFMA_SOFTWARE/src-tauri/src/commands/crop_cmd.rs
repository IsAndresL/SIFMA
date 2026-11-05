// SIFMA — Comandos IPC: Perfiles de Cultivo
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone)]
pub struct CropProfileDTO {
    pub id: i32,
    pub name: String,
    pub temp_min: f64,
    pub temp_opt: f64,
    pub temp_max: f64,
    pub ph_min: f64,
    pub ph_max: f64,
    pub ec_min: i32,
    pub ec_max: i32,
    pub cycle_days: i32,
    pub active: bool,
}

#[tauri::command]
pub fn get_crop_profiles() -> Vec<CropProfileDTO> {
    vec![
        CropProfileDTO {
            id: 1,
            name: "Cebollín (Allium fistulosum)".into(),
            temp_min: 18.0,
            temp_opt: 24.0,
            temp_max: 30.0,
            ph_min: 6.0,
            ph_max: 6.8,
            ec_min: 1000,
            ec_max: 1500,
            cycle_days: 60,
            active: true,
        },
        CropProfileDTO {
            id: 2,
            name: "Albahaca (Ocimum basilicum)".into(),
            temp_min: 20.0,
            temp_opt: 25.0,
            temp_max: 32.0,
            ph_min: 5.8,
            ph_max: 6.5,
            ec_min: 1200,
            ec_max: 1800,
            cycle_days: 45,
            active: false,
        },
    ]
}

