// SIFMA — Orquestador del Proceso Subordinado Python (Sidecar IPC)
// Ejecuta el motor científico en Python mediante JSON-RPC 2.0 sobre stdin/stdout.

use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use serde_json::{json, Value};

pub struct SidecarRunner;

impl SidecarRunner {
    /// Resuelve la ruta absoluta o relativa hacia python_engine/main_sidecar.py
    pub fn resolve_script_path() -> PathBuf {
        let candidates = [
            "../python_engine/main_sidecar.py",
            "python_engine/main_sidecar.py",
            "SIFMA_SOFTWARE/python_engine/main_sidecar.py",
        ];
        for path_str in candidates {
            let p = PathBuf::from(path_str);
            if p.exists() {
                return p;
            }
        }
        PathBuf::from("../python_engine/main_sidecar.py")
    }

    /// Invoca un método en el Sidecar de Python usando JSON-RPC 2.0 sobre stdio
    pub fn call_method(method: &str, params: Value) -> Result<Value, String> {
        let script_path = Self::resolve_script_path();
        if !script_path.exists() {
            return Err(format!("No se encontró el script del Sidecar en {:?}", script_path));
        }

        let mut child = Command::new("python")
            .arg(&script_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("Fallo al iniciar proceso Python: {}", e))?;

        let req_payload = json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        });

        if let Some(mut stdin) = child.stdin.take() {
            let line = format!("{}\n", req_payload.to_string());
            stdin
                .write_all(line.as_bytes())
                .map_err(|e| format!("Error escribiendo en stdin de Python: {}", e))?;
            let _ = stdin.flush();
        }

        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| "No se pudo capturar stdout del Sidecar".to_string())?;
        let mut reader = BufReader::new(stdout);
        let mut response_line = String::new();

        reader
            .read_line(&mut response_line)
            .map_err(|e| format!("Error leyendo stdout de Python: {}", e))?;

        let _ = child.kill();
        let _ = child.wait();

        let parsed: Value = serde_json::from_str(response_line.trim())
            .map_err(|e| format!("Respuesta JSON inválida del Sidecar: {} ({})", e, response_line))?;

        if let Some(err_obj) = parsed.get("error") {
            if !err_obj.is_null() {
                return Err(format!("Error reportado por Python Sidecar: {}", err_obj));
            }
        }

        parsed
            .get("result")
            .cloned()
            .ok_or_else(|| "Respuesta sin campo 'result'".to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sidecar_ping_and_vision_ipc() {
        let ping_res = SidecarRunner::call_method("ping", json!({})).expect("Fallo en ping IPC");
        assert_eq!(ping_res["status"], "pong");

        let vision_res = SidecarRunner::call_method(
            "process_image",
            json!({
                "image_path": "",
                "is_lateral": false,
                "pixel_to_cm_ratio": 0.05
            }),
        )
        .expect("Fallo en process_image IPC");

        assert_eq!(vision_res["success"], true);
        assert!(vision_res["biometrics"]["foliar_area_cm2"].as_f64().unwrap_or(0.0) > 0.0);
    }
}
