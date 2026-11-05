// SIFMA — Infraestructura Serial
pub mod ports;
pub mod parser;

pub use ports::SerialPortScanner;
pub use parser::{ParsedSerialFrame, SerialFrameParser};
