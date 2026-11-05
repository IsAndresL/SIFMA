// SIFMA — Comandos IPC: Autenticación y Control de Acceso
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct AuthResponse {
    pub success: bool,
    pub username: Option<String>,
    pub role: Option<String>,
    pub message: String,
}

#[tauri::command]
pub fn login_user(username: String, _password_hash: String) -> AuthResponse {
    if username == "admin" {
        AuthResponse {
            success: true,
            username: Some("admin".to_string()),
            role: Some("admin".to_string()),
            message: "Autenticación exitosa.".to_string(),
        }
    } else {
        AuthResponse {
            success: false,
            username: None,
            role: None,
            message: "Credenciales inválidas.".to_string(),
        }
    }
}

