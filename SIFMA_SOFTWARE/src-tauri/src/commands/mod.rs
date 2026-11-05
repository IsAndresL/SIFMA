// SIFMA — Módulo de Comandos IPC
pub mod system_cmd;
pub mod dashboard_cmd;
pub mod auth_cmd;
pub mod sensor_cmd;
pub mod cross_analysis_cmd;
pub mod vision_cmd;
pub mod dossier_cmd;
pub mod crop_cmd;
pub mod audit_cmd;

pub use system_cmd::*;
pub use dashboard_cmd::*;
pub use auth_cmd::*;
pub use sensor_cmd::*;
pub use cross_analysis_cmd::*;
pub use vision_cmd::*;
pub use dossier_cmd::*;
pub use crop_cmd::*;
pub use audit_cmd::*;
