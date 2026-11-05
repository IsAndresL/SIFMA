// SIFMA — Entidad de Dominio: Sesión de Captura Fotográfica en Torre
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaptureSession {
    pub id: Option<i64>,
    pub plant_id: i32,
    pub crop_type: String,
    pub session_date: String,
    pub period: String,
    pub raw_cenital_path: Option<String>,
    pub raw_lateral_path: Option<String>,
    pub processed_cenital_path: Option<String>,
    pub processed_lateral_path: Option<String>,
    pub notes: Option<String>,
}
