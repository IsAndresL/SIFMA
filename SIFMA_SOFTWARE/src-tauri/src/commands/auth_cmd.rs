// SIFMA — Comandos IPC: Autenticación y Control de Acceso
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct AuthResponse {
    pub success: bool,
    pub username: Option<String>,
    pub role: Option<String>,
    pub message: String,
}

#[derive(Serialize, Deserialize)]
pub struct UserItemDTO {
    pub id: i32,
    pub username: String,
    pub role: String,
    pub full_name: String,
    pub active: bool,
    pub created_at: String,
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

#[tauri::command]
pub fn get_users_list() -> Vec<UserItemDTO> {
    vec![
        UserItemDTO {
            id: 1,
            username: "admin".into(),
            role: "ADMINISTRADOR".into(),
            full_name: "Andrés Felipe Luna Camargo".into(),
            active: true,
            created_at: "2026-10-01".into(),
        },
        UserItemDTO {
            id: 2,
            username: "cpena".into(),
            role: "INVESTIGADOR".into(),
            full_name: "Cristian David Peña Martínez".into(),
            active: true,
            created_at: "2026-10-05".into(),
        },
        UserItemDTO {
            id: 3,
            username: "cdeluque".into(),
            role: "DIRECTOR CIENTÍFICO".into(),
            full_name: "Prof. Críspulo Enrique Deluque".into(),
            active: true,
            created_at: "2026-10-12".into(),
        },
    ]
}
