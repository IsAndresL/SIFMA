// SIFMA — Decodificador Determinista de Tramas Seriales ($pH,EC,Turb,DO,T_agua,T_ext,HR,Motor#)
// Procesa telemetría de hardware a nivel nativo con validación de integridad.

#[derive(Debug, Clone, PartialEq)]
pub struct ParsedSerialFrame {
    pub ph: f64,
    pub ec: f64,
    pub turbidity: f64,
    pub dissolved_oxygen: f64,
    pub water_temp: f64,
    pub air_temp: f64,
    pub humidity: f64,
    pub pump_active: bool,
}

pub struct SerialFrameParser;

impl SerialFrameParser {
    /// Decodifica una trama con formato "$pH,EC,Turb,DO,T_agua,T_ext,HR,Motor#"
    pub fn parse_frame(raw: &str) -> Result<ParsedSerialFrame, String> {
        let trimmed = raw.trim();
        let inner = trimmed
            .strip_prefix('$')
            .and_then(|s| s.strip_suffix('#'))
            .ok_or_else(|| "Delimitadores de trama inválidos ($...#)".to_string())?;

        let parts: Vec<&str> = inner.split(',').collect();
        if parts.len() != 8 {
            return Err(format!("Se esperaban 8 campos, se recibieron {}", parts.len()));
        }

        let parse_val = |idx: usize, name: &str| -> Result<f64, String> {
            parts[idx]
                .trim()
                .parse::<f64>()
                .map_err(|_| format!("Valor numérico inválido en campo {}", name))
        };

        let ph = parse_val(0, "pH")?;
        let ec = parse_val(1, "EC")?;
        let turbidity = parse_val(2, "Turb")?;
        let dissolved_oxygen = parse_val(3, "DO")?;
        let water_temp = parse_val(4, "T_agua")?;
        let air_temp = parse_val(5, "T_ext")?;
        let humidity = parse_val(6, "HR")?;
        let motor_raw = parts[7].trim();
        let pump_active = motor_raw == "1" || motor_raw.eq_ignore_ascii_case("ON") || motor_raw.eq_ignore_ascii_case("TRUE");

        Ok(ParsedSerialFrame {
            ph,
            ec,
            turbidity,
            dissolved_oxygen,
            water_temp,
            air_temp,
            humidity,
            pump_active,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_valid_frame() {
        let frame = "$6.24,1250.5,2.1,7.4,24.2,28.5,64.0,1#";
        let parsed = SerialFrameParser::parse_frame(frame).unwrap();
        assert!((parsed.ph - 6.24).abs() < 1e-6);
        assert!((parsed.ec - 1250.5).abs() < 1e-6);
        assert!(parsed.pump_active);
    }

    #[test]
    fn test_stress_10000_frames_zero_loss() {
        let mut success_count = 0;
        for i in 0..10_000 {
            let ph = 6.0 + (i % 100) as f64 * 0.01;
            let raw = format!("${:.2},1240.0,1.8,7.5,24.0,27.5,65.0,1#\r\n", ph);
            if SerialFrameParser::parse_frame(&raw).is_ok() {
                success_count += 1;
            }
        }
        assert_eq!(success_count, 10_000);
    }
}
