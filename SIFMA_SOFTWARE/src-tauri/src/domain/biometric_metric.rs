// SIFMA — Entidad de Dominio: Métricas Morfométricas y Fenotípicas
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiometricMetric {
    pub id: Option<i64>,
    pub session_id: i64,
    pub foliar_area_cm2: f64,
    pub plant_height_cm: f64,
    pub stem_diameter_mm: f64,
    pub health_index: f64,
    pub compacity_index: f64,
    pub fruits_count: i32,
    pub measurement_time: String,
}

