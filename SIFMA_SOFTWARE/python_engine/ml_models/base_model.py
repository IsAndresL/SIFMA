# SIFMA — Interfaz Base para Modelos de Machine Learning y Deep Learning
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np

class BaseMLModel(ABC):
    """
    Contrato abstracto unificado para todos los modelos de Inteligencia Artificial (SOLID: OCP, ISP).
    Permite intercambiar backends (PyTorch, ONNX Runtime, TensorFlow) sin alterar el sidecar.
    """

    @abstractmethod
    def load(self, model_path: str) -> bool:
        """Carga los pesos del modelo en memoria o GPU."""
        pass

    @abstractmethod
    def predict(self, input_tensor_or_image: np.ndarray) -> Dict[str, Any]:
        """Ejecuta inferencia y retorna detecciones, clasificaciones o segmentaciones."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Retorna información del modelo: nombre, versión, arquitectura y clases soportadas."""
        pass

