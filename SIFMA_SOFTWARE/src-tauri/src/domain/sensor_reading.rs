// SIFMA — Entidad de Dominio: Lectura de Telemetría Ambiental y Fisicoquímica
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorReading {
    pub id: Option<i64>,
    pub session_id: Option<i64>,
    pub reading_time: String,
    pub water_temperature: f64,
    pub exterior_temperature: f64,
    pub exterior_humidity: f64,
    pub ph: f64,
    pub electrical_conductivity: f64,
    pub turbidity: f64,
    pub dissolved_oxygen: f64,
    pub motor_status: i32,
    pub pump_current: f64,
    pub solar_radiation: f64,
}

impl SensorReading {
    pub fn is_ph_optimal(&self) -> bool {
        self.ph >= 5.5 && self.ph <= 6.8
    }

    pub fn is_ec_optimal(&self) -> bool {
        self.electrical_conductivity >= 800.0 && self.electrical_conductivity <= 1800.0
    }
}

