// SIFMA — Entidad de Dominio: Perfil de Cultivo y Calibración Óptica
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CropProfile {
    pub id: Option<i64>,
    pub crop_type: String,
    pub display_name: String,
    pub pixel_to_cm_ratio: f64,
    pub h_min: i32,
    pub h_max: i32,
    pub s_min: i32,
    pub s_max: i32,
    pub v_min: i32,
    pub v_max: i32,
    pub min_area: f64,
    pub max_area: f64,
    pub circle_center_x: Option<i32>,
    pub circle_center_y: Option<i32>,
    pub circle_radius: Option<i32>,
}

impl CropProfile {
    pub fn new_cebollin() -> Self {
        Self {
            id: None,
            crop_type: "cebollin".to_string(),
            display_name: "Cebollín (Allium fistulosum)".to_string(),
            pixel_to_cm_ratio: 0.0035,
            h_min: 24,
            h_max: 90,
            s_min: 30,
            s_max: 255,
            v_min: 30,
            v_max: 255,
            min_area: 5.0,
            max_area: 250.0,
            circle_center_x: Some(960),
            circle_center_y: Some(540),
            circle_radius: Some(450),
        }
    }
}

