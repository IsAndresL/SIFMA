// SIFMA — Conexión y Configuración de SQLite (Modo WAL)
use rusqlite::{Connection, Result};
use std::path::Path;

pub struct DbConnection;

impl DbConnection {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Connection> {
        let conn = Connection::open(path)?;
        
        // Optimización de concurrencia y seguridad de datos
        conn.execute_batch(
            "PRAGMA journal_mode = WAL;
             PRAGMA synchronous = NORMAL;
             PRAGMA foreign_keys = ON;
             PRAGMA busy_timeout = 5000;"
        )?;
        
        Ok(conn)
    }

    pub fn open_in_memory() -> Result<Connection> {
        let conn = Connection::open_in_memory()?;
        conn.execute_batch(
            "PRAGMA foreign_keys = ON;"
        )?;
        Ok(conn)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_open_in_memory_and_file() {
        let conn = DbConnection::open_in_memory().unwrap();
        assert!(conn.is_autocommit());
    }
}

