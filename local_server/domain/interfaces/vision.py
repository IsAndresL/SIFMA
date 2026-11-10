# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

from typing import Protocol, List, Dict, Any, Optional
import numpy as np
from domain.models import CropProfile

class ISegmentationStrategy(Protocol):
    """Contrato para estrategias de segmentación de imágenes (Pattern: Strategy)."""
    def create_mask(self, image: np.ndarray, profile: CropProfile, is_lateral: bool = False) -> Optional[np.ndarray]: ...
    def extract_contours(self, mask: np.ndarray, min_area: int = 30) -> List[np.ndarray]: ...

class IBiometricCalculator(Protocol):
    """Contrato para cálculo de morfometría e índices agronómicos."""
    def calculate_cenital(self, image: np.ndarray, mask: np.ndarray, contours: List[np.ndarray], profile: CropProfile, config: Optional[Any] = None) -> Dict[str, Any]: ...
    def calculate_lateral(self, image: np.ndarray, mask: np.ndarray, contours: List[np.ndarray], profile: CropProfile, config: Optional[Any] = None) -> Dict[str, Any]: ...

class IVisionPipeline(Protocol):
    """Contrato del orquestador del pipeline visual."""
    def process_cenital(self, image_path: str, output_path: str, profile: CropProfile, config: Optional[Any] = None) -> Optional[Dict[str, Any]]: ...
    def process_lateral(self, image_path: str, output_path: str, profile: CropProfile, config: Optional[Any] = None) -> Optional[Dict[str, Any]]: ...
    def filter_and_average(self, cenital_results: List[Dict[str, Any]], lateral_results: List[Dict[str, Any]]) -> Dict[str, Any]: ...

class IPhytoAIAnalyzer(Protocol):
    """Contrato para el motor híbrido de IA Fitopatológica y Visión Espectral (ONNX + K-Means)."""
    def analyze_canopy_spectrum_and_tissues(
        self,
        image_bgr: np.ndarray,
        plant_mask: np.ndarray,
        roi_circle: Optional[ Any ] = None,
        spectral_output_path: Optional[str] = None
    ) -> Dict[str, Any]: ...
    def infer_multimodal_diagnosis(
        self,
        spectral_metrics: Dict[str, Any],
        sensor_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]: ...
