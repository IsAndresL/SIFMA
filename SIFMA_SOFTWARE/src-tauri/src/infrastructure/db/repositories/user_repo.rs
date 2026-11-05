// SIFMA — Repositorio SQLite: Usuarios y Autenticación RBAC
use crate::domain::{User, UserRole};
use rusqlite::{params, Connection, Result};
use sha2::{Digest, Sha256};

pub struct UserRepository;

impl UserRepository {
    pub fn authenticate(conn: &Connection, username_or_email: &str, password: &str) -> Result<Option<User>> {
        let mut hasher = Sha256::new();
        hasher.update(password.as_bytes());
        let hash_hex = format!("{:x}", hasher.finalize());

        let mut stmt = conn.prepare(
            "SELECT id, username, email, password_hash, name, role, is_active, created_at
             FROM users
             WHERE (username = ?1 OR email = ?1) AND password_hash = ?2 AND is_active = 1
             LIMIT 1",
        )?;

        let mut rows = stmt.query(params![username_or_email, hash_hex])?;
        if let Some(row) = rows.next()? {
            let role_str: String = row.get(5)?;
            Ok(Some(User {
                id: Some(row.get(0)?),
                username: row.get(1)?,
                email: row.get(2)?,
                password_hash: row.get(3)?,
                name: row.get(4)?,
                role: UserRole::from_str(&role_str),
                is_active: row.get::<_, i32>(6)? == 1,
                created_at: row.get(7)?,
            }))
        } else {
            Ok(None)
        }
    }

    pub fn get_all(conn: &Connection) -> Result<Vec<User>> {
        let mut stmt = conn.prepare(
            "SELECT id, username, email, password_hash, name, role, is_active, created_at
             FROM users ORDER BY id ASC",
        )?;

        let rows = stmt.query_map([], |row| {
            let role_str: String = row.get(5)?;
            Ok(User {
                id: Some(row.get(0)?),
                username: row.get(1)?,
                email: row.get(2)?,
                password_hash: row.get(3)?,
                name: row.get(4)?,
                role: UserRole::from_str(&role_str),
                is_active: row.get::<_, i32>(6)? == 1,
                created_at: row.get(7)?,
            })
        })?;

        let mut users = Vec::new();
        for u in rows {
            users.push(u?);
        }
        Ok(users)
    }
}
