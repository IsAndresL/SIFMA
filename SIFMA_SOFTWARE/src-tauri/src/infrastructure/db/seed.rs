// SIFMA — Sembrado Automático de Datos Iniciales (Perfiles Botánicos y Admin)
use rusqlite::{params, Connection, Result};
use sha2::{Digest, Sha256};

pub fn seed_initial_data(conn: &Connection) -> Result<()> {
    // 1. Sembrar Administrador por defecto si la tabla está vacía
    let user_count: i64 = conn.query_row("SELECT COUNT(*) FROM users", [], |row| row.get(0))?;
    if user_count == 0 {
        let mut hasher = Sha256::new();
        hasher.update(b"admin123");
        let hash_hex = format!("{:x}", hasher.finalize());

        conn.execute(
            "INSERT INTO users (username, email, password_hash, name, role, is_active)
             VALUES (?1, ?2, ?3, ?4, ?5, 1)",
            params![
                "admin",
                "admin@sifma.local",
                hash_hex,
                "Administrador SIFMA",
                "admin"
            ],
        )?;
    }

    // 2. Sembrar Perfiles de Cultivo si no existen
    let profile_count: i64 = conn.query_row("SELECT COUNT(*) FROM crop_profile", [], |row| row.get(0))?;
    if profile_count == 0 {
        let default_profiles = [
            ("cebollin", "Cebollín (Allium fistulosum)", 0.0035, 24, 90, 30, 255, 30, 255, 5.0, 250.0),
            ("lechuga", "Lechuga Romana (Lactuca sativa)", 0.0038, 28, 88, 35, 255, 40, 255, 15.0, 600.0),
            ("albahaca", "Albahaca Genovesa (Ocimum basilicum)", 0.0032, 25, 92, 40, 255, 30, 255, 8.0, 350.0),
            ("cilantro", "Cilantro (Coriandrum sativum)", 0.0030, 26, 90, 35, 255, 35, 255, 5.0, 200.0),
            ("tomate_cherry", "Tomate Cherry (Solanum lycopersicum)", 0.0042, 22, 95, 45, 255, 30, 255, 20.0, 800.0),
            ("fresa", "Fresa Hidropónica (Fragaria ananassa)", 0.0036, 25, 90, 35, 255, 35, 255, 10.0, 400.0),
        ];

        for p in default_profiles.iter() {
            conn.execute(
                "INSERT INTO crop_profile (crop_type, display_name, pixel_to_cm_ratio, h_min, h_max, s_min, s_max, v_min, v_max, min_area, max_area)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
                params![p.0, p.1, p.2, p.3, p.4, p.5, p.6, p.7, p.8, p.9, p.10],
            )?;
        }
    }

    // 3. Sembrar Configuración Inicial
    let config_count: i64 = conn.query_row("SELECT COUNT(*) FROM config", [], |row| row.get(0))?;
    if config_count == 0 {
        conn.execute(
            "INSERT INTO config (current_plant_id, current_crop_type, camera_height_cm, camera_distance_cm, com_port, baud_rate)
             VALUES (1, 'cebollin', 65.0, 40.0, 'COM3', 9600)",
            [],
        )?;
    }

    Ok(())
}

