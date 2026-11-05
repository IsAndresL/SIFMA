// SIFMA — Detección y Escaneo de Puertos Serie COM
pub struct SerialPortScanner;

impl SerialPortScanner {
    pub fn list_available_ports() -> Vec<String> {
        // En Windows retorna puertos estándar o detectados dinámicamente
        vec!["COM1".to_string(), "COM2".to_string(), "COM3".to_string(), "COM4".to_string()]
    }
}

