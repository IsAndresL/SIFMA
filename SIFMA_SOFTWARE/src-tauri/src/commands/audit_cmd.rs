// SIFMA — Comandos IPC: Auditoría y Seguridad Criptográfica
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct AuditLogItemDTO {
    pub id: i32,
    pub timestamp: String,
    pub user: String,
    pub event_type: String,
    pub ip: String,
    pub resource: String,
    pub status: String,
    pub hash: String,
}

#[tauri::command]
pub fn get_audit_logs() -> Vec<AuditLogItemDTO> {
    vec![
        AuditLogItemDTO {
            id: 1,
            timestamp: "2026-11-05 00:01:12".into(),
            user: "admin".into(),
            event_type: "AUTH_SUCCESS".into(),
            ip: "127.0.0.1".into(),
            resource: "/login".into(),
            status: "OK".into(),
            hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855".into(),
        },
        AuditLogItemDTO {
            id: 2,
            timestamp: "2026-11-04 23:45:00".into(),
            user: "system".into(),
            event_type: "TELEMETRY_INGEST".into(),
            ip: "COM3".into(),
            resource: "/serial".into(),
            status: "OK".into(),
            hash: "5b992e34b3d1521ac9ac66465720fcf4f8b2556532f5ec1391699b612864213d".into(),
        },
    ]
}

