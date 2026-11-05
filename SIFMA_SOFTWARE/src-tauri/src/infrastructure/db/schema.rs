// SIFMA — DDL y Esquema de Base de Datos SQLite
use rusqlite::{Connection, Result};

pub fn initialize_schema(conn: &Connection) -> Result<()> {
    conn.execute_batch(
        "
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'invitado',
            avatar_path TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS crop_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_type TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            pixel_to_cm_ratio REAL NOT NULL DEFAULT 0.0035,
            h_min INTEGER NOT NULL DEFAULT 24,
            h_max INTEGER NOT NULL DEFAULT 90,
            s_min INTEGER NOT NULL DEFAULT 30,
            s_max INTEGER NOT NULL DEFAULT 255,
            v_min INTEGER NOT NULL DEFAULT 30,
            v_max INTEGER NOT NULL DEFAULT 255,
            min_area REAL NOT NULL DEFAULT 5.0,
            max_area REAL NOT NULL DEFAULT 250.0,
            circle_center_x INTEGER DEFAULT 960,
            circle_center_y INTEGER DEFAULT 540,
            circle_radius INTEGER DEFAULT 450
        );

        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_plant_id INTEGER NOT NULL DEFAULT 1,
            current_crop_type TEXT NOT NULL DEFAULT 'cebollin',
            camera_height_cm REAL DEFAULT 65.0,
            camera_distance_cm REAL DEFAULT 40.0,
            com_port TEXT DEFAULT 'COM3',
            baud_rate INTEGER DEFAULT 9600
        );

        CREATE TABLE IF NOT EXISTS capture_session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL DEFAULT 1,
            crop_type TEXT NOT NULL,
            session_date TEXT NOT NULL,
            period TEXT NOT NULL,
            raw_cenital_path TEXT,
            raw_lateral_path TEXT,
            processed_cenital_path TEXT,
            processed_lateral_path TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS biometric_metric (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            foliar_area_cm2 REAL NOT NULL DEFAULT 0.0,
            plant_height_cm REAL NOT NULL DEFAULT 0.0,
            stem_diameter_mm REAL NOT NULL DEFAULT 0.0,
            health_index REAL NOT NULL DEFAULT 0.0,
            compacity_index REAL NOT NULL DEFAULT 0.0,
            fruits_count INTEGER NOT NULL DEFAULT 0,
            measurement_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (session_id) REFERENCES capture_session(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS sensor_reading (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            reading_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            water_temperature REAL NOT NULL DEFAULT 0.0,
            exterior_temperature REAL NOT NULL DEFAULT 0.0,
            exterior_humidity REAL NOT NULL DEFAULT 0.0,
            ph REAL NOT NULL DEFAULT 7.0,
            electrical_conductivity REAL NOT NULL DEFAULT 0.0,
            turbidity REAL NOT NULL DEFAULT 0.0,
            dissolved_oxygen REAL NOT NULL DEFAULT 0.0,
            motor_status INTEGER NOT NULL DEFAULT 0,
            pump_current REAL NOT NULL DEFAULT 0.0,
            solar_radiation REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (session_id) REFERENCES capture_session(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS agronomic_conclusion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL,
            conclusion_date TEXT NOT NULL,
            title TEXT NOT NULL,
            observation TEXT NOT NULL,
            recommendations TEXT,
            author_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            description TEXT,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        "
    )?;

    Ok(())
}
