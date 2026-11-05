// SIFMA — Repositorio SQLite: Perfiles de Cultivo
use crate::domain::CropProfile;
use rusqlite::{params, Connection, Result};

pub struct CropRepository;

impl CropRepository {
    pub fn get_all(conn: &Connection) -> Result<Vec<CropProfile>> {
        let mut stmt = conn.prepare(
            "SELECT id, crop_type, display_name, pixel_to_cm_ratio, h_min, h_max,
                    s_min, s_max, v_min, v_max, min_area, max_area, circle_center_x,
                    circle_center_y, circle_radius
             FROM crop_profile ORDER BY id ASC",
        )?;

        let rows = stmt.query_map([], |row| {
            Ok(CropProfile {
                id: Some(row.get(0)?),
                crop_type: row.get(1)?,
                display_name: row.get(2)?,
                pixel_to_cm_ratio: row.get(3)?,
                h_min: row.get(4)?,
                h_max: row.get(5)?,
                s_min: row.get(6)?,
                s_max: row.get(7)?,
                v_min: row.get(8)?,
                v_max: row.get(9)?,
                min_area: row.get(10)?,
                max_area: row.get(11)?,
                circle_center_x: row.get(12)?,
                circle_center_y: row.get(13)?,
                circle_radius: row.get(14)?,
            })
        })?;

        let mut profiles = Vec::new();
        for profile in rows {
            profiles.push(profile?);
        }
        Ok(profiles)
    }

    pub fn get_by_crop_type(conn: &Connection, crop_type: &str) -> Result<Option<CropProfile>> {
        let mut stmt = conn.prepare(
            "SELECT id, crop_type, display_name, pixel_to_cm_ratio, h_min, h_max,
                    s_min, s_max, v_min, v_max, min_area, max_area, circle_center_x,
                    circle_center_y, circle_radius
             FROM crop_profile WHERE crop_type = ?1 LIMIT 1",
        )?;

        let mut rows = stmt.query(params![crop_type])?;
        if let Some(row) = rows.next()? {
            Ok(Some(CropProfile {
                id: Some(row.get(0)?),
                crop_type: row.get(1)?,
                display_name: row.get(2)?,
                pixel_to_cm_ratio: row.get(3)?,
                h_min: row.get(4)?,
                h_max: row.get(5)?,
                s_min: row.get(6)?,
                s_max: row.get(7)?,
                v_min: row.get(8)?,
                v_max: row.get(9)?,
                min_area: row.get(10)?,
                max_area: row.get(11)?,
                circle_center_x: row.get(12)?,
                circle_center_y: row.get(13)?,
                circle_radius: row.get(14)?,
            }))
        } else {
            Ok(None)
        }
    }
}
