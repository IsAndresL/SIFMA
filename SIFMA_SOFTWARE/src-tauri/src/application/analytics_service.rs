// SIFMA — Servicio de Analítica Matemática y Correlación de Pearson en Rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DescriptiveStats {
    pub count: usize,
    pub mean: f64,
    pub std_dev: f64,
    pub median: f64,
    pub iqr: f64,
    pub cv_percent: f64,
}

pub struct AnalyticsService;

impl AnalyticsService {
    /// Calcula el Coeficiente de Correlación de Pearson (r) entre dos series numéricas
    pub fn calculate_pearson(x: &[f64], y: &[f64]) -> Option<f64> {
        if x.len() != y.len() || x.len() < 2 {
            return None;
        }

        let n = x.len() as f64;
        let mean_x = x.iter().sum::<f64>() / n;
        let mean_y = y.iter().sum::<f64>() / n;

        let mut numerator = 0.0;
        let mut denom_x = 0.0;
        let mut denom_y = 0.0;

        for (xi, yi) in x.iter().zip(y.iter()) {
            let dx = xi - mean_x;
            let dy = yi - mean_y;
            numerator += dx * dy;
            denom_x += dx * dx;
            denom_y += dy * dy;
        }

        let denominator = (denom_x * denom_y).sqrt();
        if denominator.abs() < 1e-12 {
            return Some(0.0);
        }

        Some(numerator / denominator)
    }

    /// Calcula estadísticas descriptivas completas
    pub fn calculate_descriptive(values: &[f64]) -> Option<DescriptiveStats> {
        if values.is_empty() {
            return None;
        }

        let n = values.len();
        let mean = values.iter().sum::<f64>() / (n as f64);

        let variance = if n > 1 {
            values.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / ((n - 1) as f64)
        } else {
            0.0
        };
        let std_dev = variance.sqrt();

        let mut sorted = values.to_vec();
        sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());

        let median = if n % 2 == 0 {
            (sorted[n / 2 - 1] + sorted[n / 2]) / 2.0
        } else {
            sorted[n / 2]
        };

        let q1 = sorted[(n as f64 * 0.25) as usize];
        let q3 = sorted[(n as f64 * 0.75).min((n - 1) as f64) as usize];
        let iqr = q3 - q1;

        let cv_percent = if mean.abs() > 1e-6 {
            (std_dev / mean) * 100.0
        } else {
            0.0
        };

        Some(DescriptiveStats {
            count: n,
            mean,
            std_dev,
            median,
            iqr,
            cv_percent,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pearson_perfect_correlation() {
        let x = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let y = vec![2.0, 4.0, 6.0, 8.0, 10.0];
        let r = AnalyticsService::calculate_pearson(&x, &y).unwrap();
        assert!((r - 1.0).abs() < 1e-6);
    }

    #[test]
    fn test_descriptive_stats() {
        let data = vec![10.0, 12.0, 14.0, 16.0, 18.0];
        let stats = AnalyticsService::calculate_descriptive(&data).unwrap();
        assert_eq!(stats.mean, 14.0);
        assert_eq!(stats.median, 14.0);
    }
}

