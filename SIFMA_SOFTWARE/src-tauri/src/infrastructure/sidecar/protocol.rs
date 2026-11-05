// SIFMA — Protocolo de Mensajería IPC para Motor Python (Sidecar)
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SidecarRequest {
    pub id: String,
    pub command: String,
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SidecarResponse {
    pub id: String,
    pub status: String,
    pub data: Option<serde_json::Value>,
    pub error: Option<String>,
}
