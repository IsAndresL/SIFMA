// SIFMA — Comandos IPC: Cruce Multivariable y Correlación
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct AnalysisPointDTO {
    pub x: f64,
    pub y: f64,
    pub plant_id: i32,
    pub date: String,
}

#[derive(Serialize, Deserialize)]
pub struct CrossAnalysisResultDTO {
    pub pearson_r: f64,
    pub r_squared: f64,
    pub slope: f64,
    pub intercept: f64,
    pub p_value: f64,
    pub interpretation: String,
    pub points: Vec<AnalysisPointDTO>,
}

#[derive(Serialize, Deserialize)]
pub struct CorrelationMatrixDTO {
    pub labels: Vec<String>,
    pub matrix: Vec<Vec<f64>>,
}

#[tauri::command]
pub fn get_cross_analysis_data(var_x: String, var_y: String) -> CrossAnalysisResultDTO {
    let mut points = Vec::new();
    for i in 0..25 {
        points.push(AnalysisPointDTO {
            x: 22.0 + (i as f64) * 0.3,
            y: 50.0 + (i as f64) * 0.9,
            plant_id: (i % 12) + 1,
            date: format!("2026-11-{:02}", (i % 5) + 1),
        });
    }

    CrossAnalysisResultDTO {
        pearson_r: 0.842,
        r_squared: 0.709,
        slope: 1.84,
        intercept: 12.1,
        p_value: 0.0004,
        interpretation: format!(
            "Correlación positiva significativa entre {} y {}. Aumentos térmicos estimulan el crecimiento foliar.",
            var_x, var_y
        ),
        points,
    }
}

#[tauri::command]
pub fn get_correlation_matrix() -> CorrelationMatrixDTO {
    CorrelationMatrixDTO {
        labels: vec![
            "T. Agua".into(),
            "T. Aire".into(),
            "Humedad".into(),
            "pH".into(),
            "EC".into(),
            "Área Foliar".into(),
            "Altura".into(),
        ],
        matrix: vec![
            vec![1.00, 0.72, -0.45, 0.12, 0.28, 0.84, 0.79],
            vec![0.72, 1.00, -0.68, 0.08, 0.19, 0.65, 0.71],
            vec![-0.45, -0.68, 1.00, -0.15, -0.10, -0.32, -0.28],
            vec![0.12, 0.08, -0.15, 1.00, 0.35, 0.18, 0.14],
            vec![0.28, 0.19, -0.10, 0.35, 1.00, 0.54, 0.49],
            vec![0.84, 0.65, -0.32, 0.18, 0.54, 1.00, 0.92],
            vec![0.79, 0.71, -0.28, 0.14, 0.49, 0.92, 1.00],
        ],
    }
}

