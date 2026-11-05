// SIFMA — Repositorio SQLite: Lecturas de Telemetría
use crate::domain::SensorReading;
use rusqlite::{params, Connection, Result};

pub struct SensorRepository;

impl SensorRepository {
    pub fn insert(conn: &Connection, r: &SensorReading) -> Result<i64> {
        conn.execute(
            "INSERT INTO sensor_reading (
                session_id, reading_time, water_temperature, exterior_temperature,
                exterior_humidity, ph, electrical_conductivity, turbidity,
                dissolved_oxygen, motor_status, pump_current, solar_radiation
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
            params![
                r.session_id,
                r.reading_time,
                r.water_temperature,
                r.exterior_temperature,
                r.exterior_humidity,
                r.ph,
                r.electrical_conductivity,
                r.turbidity,
                r.dissolved_oxygen,
                r.motor_status,
                r.pump_current,
                r.solar_radiation
            ],
        )?;

        Ok(conn.last_insert_rowid())
    }

    pub fn get_latest(conn: &Connection) -> Result<Option<SensorReading>> {
        let mut stmt = conn.prepare(
            "SELECT id, session_id, reading_time, water_temperature, exterior_temperature,
                    exterior_humidity, ph, electrical_conductivity, turbidity,
                    dissolved_oxygen, motor_status, pump_current, solar_radiation
             FROM sensor_reading
             ORDER BY id DESC LIMIT 1",
        )?;

        let mut rows = stmt.query([])?;
        if let Some(row) = rows.next()? {
            Ok(Some(SensorReading {
                id: Some(row.get(0)?),
                session_id: row.get(1)?,
                reading_time: row.get(2)?,
                water_temperature: row.get(3)?,
                exterior_temperature: row.get(4)?,
                exterior_humidity: row.get(5)?,
                ph: row.get(6)?,
                electrical_conductivity: row.get(7)?,
                turbidity: row.get(8)?,
                dissolved_oxygen: row.get(9)?,
                motor_status: row.get(10)?,
                pump_current: row.get(11)?,
                solar_radiation: row.get(12)?,
            }))
        } else {
            Ok(None)
        }
    }
}
