from typing import Protocol, List, Dict, Any, Optional

class ITelemetryAdapter(Protocol):
    """Contrato para fuentes y adaptadores de telemetría (Pattern: Adapter)."""
    def get_available_ports(self) -> List[str]: ...
    def read_sample(self) -> Dict[str, Any]: ...

class ICsvTelemetryParser(Protocol):
    """Contrato para importación y parseo de tramas y archivos de torre."""
    def parse_stream(self, file_stream) -> Dict[str, Any]: ...
