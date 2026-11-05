// SIFMA — Comandos IPC: Generación de Dossier Técnico
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct ScientificDossierDTO {
    pub title: String,
    pub cycle_code: String,
    pub species: String,
    pub total_plants: i32,
    pub total_days: i32,
    pub observations_count: i32,
    pub mean_growth_rate: String,
    pub r_temperature_foliar: f64,
    pub water_use_efficiency: String,
    pub dnda_deposit_code: String,
    pub verified_by: String,
}

#[tauri::command]
pub fn get_scientific_dossier(plant_id: Option<i32>) -> ScientificDossierDTO {
    ScientificDossierDTO {
        title: "Dossier Científico y Fenotípico de Torre Hidropónica SIFMA".into(),
        cycle_code: "CICLO-2026-A1".into(),
        species: "Allium fistulosum (Cebollín de Rama)".into(),
        total_plants: 12,
        total_days: 28,
        observations_count: 336,
        mean_growth_rate: "1.42 cm²/día".into(),
        r_temperature_foliar: 0.842,
        water_use_efficiency: "96.4%".into(),
        dnda_deposit_code: "SIFMA-DOC-ARQ-2026".into(),
        verified_by: "Administrador SIFMA / Agrónomo en Jefe".into(),
    }
}

