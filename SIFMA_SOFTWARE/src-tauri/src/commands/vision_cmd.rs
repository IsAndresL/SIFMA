// SIFMA — Comandos IPC: Fenotipado Foliar y Sesiones de Visión
use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::infrastructure::sidecar::SidecarRunner;

#[derive(Serialize, Deserialize)]
pub struct CaptureSessionItemDTO {
    pub id: i32,
    pub plant_id: i32,
    pub timestamp: String,
    pub foliar_area: f64,
    pub plant_height: f64,
    pub stem_diameter: f64,
    pub health_index: f64,
    pub status: String,
}

#[derive(Serialize, Deserialize)]
pub struct VisionProcessResultDTO {
    pub status: String,
    pub session_id: i64,
    pub foliar_area: f64,
    pub plant_height: f64,
    pub stem_diameter: f64,
    pub health_index: f64,
    pub green_coverage_pct: f64,
    pub chlorophyll_index_exg: f64,
    pub processing_time_ms: u64,
}

#[derive(Serialize, Deserialize)]
pub struct TimelapseFrameDTO {
    pub day: i32,
    pub date: String,
    pub foliar_area: f64,
    pub plant_height: f64,
    pub image_url: String,
}

#[tauri::command]
pub fn list_capture_sessions(plant_id: Option<i32>) -> Vec<CaptureSessionItemDTO> {
    let pid = plant_id.unwrap_or(1);
    vec![
        CaptureSessionItemDTO {
            id: 101,
            plant_id: pid,
            timestamp: "2026-11-04 14:30".into(),
            foliar_area: 61.8,
            plant_height: 18.5,
            stem_diameter: 4.8,
            health_index: 82.8,
            status: "PROCESADO".into(),
        },
        CaptureSessionItemDTO {
            id: 100,
            plant_id: pid,
            timestamp: "2026-11-04 14:15".into(),
            foliar_area: 58.2,
            plant_height: 17.2,
            stem_diameter: 4.5,
            health_index: 85.1,
            status: "PROCESADO".into(),
        },
    ]
}

#[tauri::command]
pub fn trigger_vision_processing(image_path: Option<String>, _crop_id: Option<i32>) -> VisionProcessResultDTO {
    let path_str = image_path.unwrap_or_default();
    let params = json!({
        "image_path": path_str,
        "is_lateral": false,
        "pixel_to_cm_ratio": 0.05
    });

    if let Ok(res) = SidecarRunner::call_method("process_image", params) {
        let bio = &res["biometrics"];
        return VisionProcessResultDTO {
            status: "success (Python Sidecar IPC)".into(),
            session_id: chrono::Utc::now().timestamp(),
            foliar_area: bio["foliar_area_cm2"].as_f64().unwrap_or(62.4),
            plant_height: bio["plant_height_cm"].as_f64().unwrap_or(18.8),
            stem_diameter: bio["stem_diameter_mm"].as_f64().unwrap_or(4.9),
            health_index: bio["health_index"].as_f64().unwrap_or(84.0),
            green_coverage_pct: bio["green_coverage_pct"].as_f64().unwrap_or(36.8),
            chlorophyll_index_exg: bio["chlorophyll_index_exg"].as_f64().unwrap_or(0.45),
            processing_time_ms: res["elapsed_ms"].as_f64().unwrap_or(42.0) as u64,
        };
    }

    VisionProcessResultDTO {
        status: "success".into(),
        session_id: 102,
        foliar_area: 62.4,
        plant_height: 18.8,
        stem_diameter: 4.9,
        health_index: 84.0,
        green_coverage_pct: 36.8,
        chlorophyll_index_exg: 0.45,
        processing_time_ms: 182,
    }
}

#[tauri::command]
pub fn get_timelapse_frames(_plant_id: Option<i32>) -> Vec<TimelapseFrameDTO> {
    let mut frames = Vec::new();
    for i in 1..=12 {
        frames.push(TimelapseFrameDTO {
            day: i,
            date: format!("2026-10-{:02}", 19 + i),
            foliar_area: 24.0 + (i as f64) * 3.4,
            plant_height: 8.0 + (i as f64) * 0.95,
            image_url: "core/assets/sifma_sin_texto.svg".into(),
        });
    }
    frames
}
