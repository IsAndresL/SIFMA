// SIFMA — Entidad de Dominio: Usuario y Control de Acceso RBAC
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum UserRole {
    Admin,
    Investigador,
    Operador,
    Invitado,
}

impl UserRole {
    pub fn from_str(role: &str) -> Self {
        match role.to_lowercase().as_str() {
            "admin" | "administrador" => UserRole::Admin,
            "investigador" => UserRole::Investigador,
            "operador" => UserRole::Operador,
            _ => UserRole::Invitado,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            UserRole::Admin => "admin",
            UserRole::Investigador => "investigador",
            UserRole::Operador => "operador",
            UserRole::Invitado => "invitado",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: Option<i64>,
    pub username: String,
    pub email: String,
    pub password_hash: String,
    pub name: String,
    pub role: UserRole,
    pub is_active: bool,
    pub created_at: String,
}
