# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

"""
Constructor y serializador binario de la Red Neuronal Ligera ONNX (SIFMA-PhytoNet v1.0).
Genera un archivo estándar `.onnx` (Open Neural Network Exchange, IR v7, Opset 11)
sin requerir dependencias pesadas externas (como PyTorch o TensorFlow), permitiendo
su ejecución directa en C++ mediante `cv2.dnn.readNetFromONNX()`.

Arquitectura de la Red Neuronal Multimodal (MLP 16 -> 24 -> 6):
  - Entrada `input_features` [1, 16] (float32):
      [0]  healthy_tissue_norm     (Proporción de tejido fotosintético vigoroso 0..1)
      [1]  chlorosis_norm          (Proporción de tejido clorótico / amarillamiento 0..1)
      [2]  necrosis_norm           (Proporción de tejido necrótico / quemadura 0..1)
      [3]  gli_index               (Green Leaf Index: (2G - R - B)/(2G + R + B))
      [4]  vari_index              (Visible Atmospherically Resistant Index: (G - R)/(G + R - B))
      [5]  exg_norm                (Excess Green Index normalizado 0..1)
      [6]  apical_damage_ratio     (Proporción de daño en bordes/ápices foliares vs centro 0..1)
      [7]  interveinal_contrast    (Contraste cromático intervenal / moteado foliar 0..1)
      [8]  ph_high_stress          (Indicador de alcalinidad de solución pH > 6.6)
      [9]  ph_low_stress           (Indicador de acidez excesiva pH < 5.4)
      [10] ec_low_stress           (Indicador de solución nutritiva diluida EC < 1200 µS/cm)
      [11] ec_high_stress          (Indicador de estrés osmótico / salinidad EC > 2400 µS/cm)
      [12] thermal_vpd_stress      (Indicador de estrés evapotranspirativo T > 28°C o HR < 50%)
      [13] root_hypoxia_stress     (Indicador de hipoxia radical DO < 5.5 mg/L o T_agua > 26°C)
      [14] low_light_stress        (Indicador de déficit lumínico UV/Lux < 180 lux)
      [15] has_telemetry_flag      (1.0 si hay sensores sincronizados, 0.0 si es solo visual)
  - Capa Oculta 1: Gemm (16 -> 24) + ReLU
  - Capa de Salida: Gemm (24 -> 6) + Softmax -> `class_probs` [1, 6]
"""

import os
import struct
from typing import List, Tuple
import numpy as np


# ==============================================================================
# Codificador Protobuf Minimalista para Especificación ONNX (IR v7, Opset 11)
# ==============================================================================

def _encode_varint(value: int) -> bytes:
    """Codifica un entero sin signo en formato Base-128 Varint de Protocol Buffers."""
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value & 0x7F)
    return bytes(out)


def _field_varint(field_num: int, value: int) -> bytes:
    tag = (field_num << 3) | 0
    return _encode_varint(tag) + _encode_varint(value)


def _field_bytes(field_num: int, data: bytes) -> bytes:
    tag = (field_num << 3) | 2
    return _encode_varint(tag) + _encode_varint(len(data)) + data


def _field_string(field_num: int, text: str) -> bytes:
    return _field_bytes(field_num, text.encode("utf-8"))


def _field_float(field_num: int, val: float) -> bytes:
    tag = (field_num << 3) | 5
    return _encode_varint(tag) + struct.pack("<f", val)


def _make_tensor_proto(name: str, dims: List[int], float_data: np.ndarray) -> bytes:
    """
    Construye un mensaje ONNX `TensorProto` (FLOAT = 1) usando `raw_data` (campo 9).
    TensorProto fields:
      - dims (1, repeated int64)
      - data_type (2, int32: 1 = FLOAT)
      - name (8, string)
      - raw_data (9, bytes)
    """
    arr = np.asarray(float_data, dtype="<f4")
    msg = bytearray()
    for d in dims:
        msg += _field_varint(1, d)
    msg += _field_varint(2, 1)  # DataType.FLOAT = 1
    msg += _field_string(8, name)
    msg += _field_bytes(9, arr.tobytes())
    return bytes(msg)


def _make_attribute_int(name: str, val: int) -> bytes:
    """
    Construye un `AttributeProto` de tipo INT (type = 2).
      - name (1, string)
      - i (3, int64)
      - type (20, AttributeType: INT = 2)
    """
    msg = bytearray()
    msg += _field_string(1, name)
    msg += _field_varint(3, val)
    msg += _field_varint(20, 2)
    return bytes(msg)


def _make_attribute_float(name: str, val: float) -> bytes:
    """
    Construye un `AttributeProto` de tipo FLOAT (type = 1).
      - name (1, string)
      - f (2, float)
      - type (20, AttributeType: FLOAT = 1)
    """
    msg = bytearray()
    msg += _field_string(1, name)
    msg += _field_float(2, val)
    msg += _field_varint(20, 1)
    return bytes(msg)


def _make_node_proto(
    op_type: str,
    inputs: List[str],
    outputs: List[str],
    name: str,
    attributes: List[bytes] = None
) -> bytes:
    """
    Construye un `NodeProto` de ONNX.
      - input (1, repeated string)
      - output (2, repeated string)
      - name (3, string)
      - op_type (4, string)
      - attribute (5, repeated AttributeProto)
    """
    msg = bytearray()
    for inp in inputs:
        msg += _field_string(1, inp)
    for out in outputs:
        msg += _field_string(2, out)
    msg += _field_string(3, name)
    msg += _field_string(4, op_type)
    if attributes:
        for attr in attributes:
            msg += _field_bytes(5, attr)
    return bytes(msg)


def _make_value_info_proto(name: str, dims: List[int]) -> bytes:
    """
    Construye un `ValueInfoProto` para tensores de entrada/salida FLOAT.
    ValueInfoProto:
      - name (1, string)
      - type (2, TypeProto)
        TypeProto:
          - tensor_type (1, TypeProto.Tensor)
            TypeProto.Tensor:
              - elem_type (1, int32: 1 = FLOAT)
              - shape (2, TensorShapeProto)
                TensorShapeProto:
                  - dim (1, repeated Dimension)
                    Dimension:
                      - dim_value (1, int64)
    """
    shape_msg = bytearray()
    for d in dims:
        dim_msg = _field_varint(1, d)
        shape_msg += _field_bytes(1, dim_msg)

    tensor_type_msg = _field_varint(1, 1) + _field_bytes(2, bytes(shape_msg))
    type_proto_msg = _field_bytes(1, tensor_type_msg)

    val_info_msg = _field_string(1, name) + _field_bytes(2, type_proto_msg)
    return bytes(val_info_msg)


def build_calibrated_weights() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Genera los pesos sinápticos calibrados agronómica y fisiológicamente
    para la red neuronal multimodal SIFMA-PhytoNet (16 -> 24 -> 6).
    """
    W1 = np.zeros((24, 16), dtype=np.float32)
    B1 = np.zeros((24,), dtype=np.float32)

    # Neuronas 0..3: Detectoras de Vigor Fotosintético y Clorofila Alta (Clase 0: OPTIMAL)
    W1[0, 0] = 3.2; W1[0, 3] = 2.5; W1[0, 4] = 2.0; W1[0, 5] = 1.8; W1[0, 1] = -3.5; W1[0, 2] = -4.0; B1[0] = 0.4
    W1[1, 0] = 2.8; W1[1, 3] = 2.2; W1[1, 8] = -2.0; W1[1, 10] = -2.0; W1[1, 11] = -2.0; W1[1, 13] = -2.0; B1[1] = 0.5
    W1[2, 0] = 2.5; W1[2, 1] = -3.0; W1[2, 2] = -3.5; W1[2, 12] = -1.5; B1[2] = 0.3
    W1[3, 3] = 3.0; W1[3, 4] = 2.5; W1[3, 1] = -2.5; W1[3, 2] = -2.5; B1[3] = 0.2

    # Neuronas 4..7: Clorosis Férrica / Bloqueo de Micronutrientes por pH Alcalino (Clase 1: FE_LOCKOUT)
    W1[4, 1] = 4.2; W1[4, 7] = 2.4; W1[4, 8] = 4.5; W1[4, 3] = -2.0; B1[4] = -0.3
    W1[5, 1] = 3.8; W1[5, 8] = 3.8; W1[5, 10] = -1.5; B1[5] = -0.2
    W1[6, 1] = 3.5; W1[6, 7] = 3.0; W1[6, 15] = -1.0; B1[6] = -0.4  # Patrón visual intervenal cuando no hay sensor
    W1[7, 8] = 3.2; W1[7, 1] = 2.2; W1[7, 0] = -1.5; B1[7] = -0.2

    # Neuronas 8..11: Deficiencia de Nitrógeno / Solución Nutritiva Diluida (Clase 2: N_DEFICIENCY)
    W1[8, 1] = 4.4; W1[8, 10] = 4.5; W1[8, 3] = -2.5; W1[8, 5] = -2.0; B1[8] = -0.3
    W1[9, 1] = 3.8; W1[9, 10] = 3.6; W1[9, 8] = -1.5; B1[9] = -0.2
    W1[10, 1] = 4.0; W1[10, 3] = -2.2; W1[10, 7] = -1.2; B1[10] = -0.35  # Clorosis uniforme generalizada
    W1[11, 10] = 3.4; W1[11, 1] = 2.4; W1[11, 0] = -1.5; B1[11] = -0.2

    # Neuronas 12..15: Quemadura Apical (Tip-Burn) por Calcio / Estrés Evapotranspirativo (Clase 3: CA_TIPBURN)
    W1[12, 2] = 4.6; W1[12, 6] = 3.5; W1[12, 12] = 4.2; B1[12] = -0.3
    W1[13, 2] = 4.2; W1[13, 6] = 3.8; W1[13, 11] = -1.5; B1[13] = -0.25
    W1[14, 2] = 3.6; W1[14, 12] = 3.5; W1[14, 4] = -2.0; B1[14] = -0.3
    W1[15, 6] = 3.2; W1[15, 2] = 3.4; B1[15] = -0.35

    # Neuronas 16..19: Fitotoxicidad Salina / Estrés Osmótico (Clase 4: SALINE_TOXICITY)
    W1[16, 2] = 4.4; W1[16, 1] = 2.2; W1[16, 11] = 4.8; B1[16] = -0.35
    W1[17, 2] = 3.8; W1[17, 11] = 4.2; W1[17, 12] = 1.5; B1[17] = -0.3
    W1[18, 2] = 4.0; W1[18, 1] = 2.8; W1[18, 4] = -2.5; B1[18] = -0.45
    W1[19, 11] = 3.8; W1[19, 2] = 2.5; B1[19] = -0.3

    # Neuronas 20..23: Hipoxia Radical / Estrés de Raíz y Déficit Lumínico (Clase 5: ROOT_HYPOXIA)
    W1[20, 13] = 4.8; W1[20, 1] = 2.5; W1[20, 2] = 2.0; B1[20] = -0.3
    W1[21, 13] = 4.2; W1[21, 0] = -1.8; B1[21] = -0.25
    W1[22, 14] = 3.2; W1[22, 1] = 2.5; W1[22, 13] = 2.8; B1[22] = -0.35
    W1[23, 9] = 3.0; W1[23, 13] = 3.2; W1[23, 1] = 2.0; B1[23] = -0.3

    # Capa de Salida W2 (6 clases x 24 neuronas ocultas)
    W2 = np.zeros((6, 24), dtype=np.float32)
    B2 = np.array([0.8, -0.4, -0.3, -0.4, -0.5, -0.5], dtype=np.float32)

    # Clase 0: OPTIMAL
    W2[0, 0:4] = [2.6, 2.4, 2.2, 1.8]
    W2[0, 4:] = -1.2

    # Clase 1: FE_LOCKOUT
    W2[1, 4:8] = [2.8, 2.5, 2.0, 2.2]
    W2[1, 0:4] = -1.5

    # Clase 2: N_DEFICIENCY
    W2[2, 8:12] = [2.8, 2.5, 2.2, 2.1]
    W2[2, 0:4] = -1.5

    # Clase 3: CA_TIPBURN
    W2[3, 12:16] = [2.9, 2.6, 2.3, 2.2]
    W2[3, 0:4] = -1.6

    # Clase 4: SALINE_TOXICITY
    W2[4, 16:20] = [2.9, 2.6, 2.1, 2.2]
    W2[4, 0:4] = -1.6

    # Clase 5: ROOT_HYPOXIA
    W2[5, 20:24] = [2.9, 2.5, 2.1, 2.2]
    W2[5, 0:4] = -1.5

    # Escalar pesos de salida para obtener distribución Softmax calibrada (85% - 97% confianza)
    W1 *= 0.55
    W2 *= 0.65
    return W1, B1, W2, B2


def ensure_onnx_model_file(model_path: str) -> str:
    """
    Garantiza que el archivo binario `.onnx` de la red neuronal SIFMA-PhytoNet exista
    en disco. Si no existe, lo compila y serializa automáticamente.
    """
    if os.path.isfile(model_path) and os.path.getsize(model_path) > 512:
        return model_path

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    W1, B1, W2, B2 = build_calibrated_weights()

    # Inicializadores (Pesos y Sesgos de la red)
    init_w1 = _make_tensor_proto("W1", [24, 16], W1)
    init_b1 = _make_tensor_proto("B1", [24], B1)
    init_w2 = _make_tensor_proto("W2", [6, 24], W2)
    init_b2 = _make_tensor_proto("B2", [6], B2)

    # Nodos computacionales ONNX
    node_gemm1 = _make_node_proto(
        op_type="Gemm",
        inputs=["input_features", "W1", "B1"],
        outputs=["hidden_linear"],
        name="fc1_gemm",
        attributes=[
            _make_attribute_int("transB", 1),
            _make_attribute_float("alpha", 1.0),
            _make_attribute_float("beta", 1.0),
        ]
    )
    node_relu1 = _make_node_proto(
        op_type="Relu",
        inputs=["hidden_linear"],
        outputs=["hidden_act"],
        name="fc1_relu"
    )
    node_gemm2 = _make_node_proto(
        op_type="Gemm",
        inputs=["hidden_act", "W2", "B2"],
        outputs=["logits"],
        name="fc2_gemm",
        attributes=[
            _make_attribute_int("transB", 1),
            _make_attribute_float("alpha", 1.0),
            _make_attribute_float("beta", 1.0),
        ]
    )
    node_softmax = _make_node_proto(
        op_type="Softmax",
        inputs=["logits"],
        outputs=["class_probs"],
        name="output_softmax",
        attributes=[_make_attribute_int("axis", 1)]
    )

    # Entradas y Salidas del Grafo
    input_vi = _make_value_info_proto("input_features", [1, 16])
    output_vi = _make_value_info_proto("class_probs", [1, 6])

    # Construcción de GraphProto:
    # node (1), name (2), initializer (5), input (11), output (12)
    graph_msg = bytearray()
    for n in (node_gemm1, node_relu1, node_gemm2, node_softmax):
        graph_msg += _field_bytes(1, n)
    graph_msg += _field_string(2, "SIFMA_PhytoNet_MLP_Graph")
    for init in (init_w1, init_b1, init_w2, init_b2):
        graph_msg += _field_bytes(5, init)
    graph_msg += _field_bytes(11, input_vi)
    graph_msg += _field_bytes(12, output_vi)

    # OpsetImportProto: domain (1, ""), version (2, 11)
    opset_msg = _field_string(1, "") + _field_varint(2, 11)

    # ModelProto:
    # ir_version (1) = 7
    # producer_name (2) = "SIFMA-AI-Engine"
    # producer_version (3) = "1.0"
    # model_version (5) = 1
    # doc_string (6) = "SIFMA Multimodal Phytopathological & Nutritional Neural Network"
    # graph (7) = graph_msg
    # opset_import (8) = opset_msg
    model_msg = bytearray()
    model_msg += _field_varint(1, 7)
    model_msg += _field_string(2, "SIFMA-AI-Engine")
    model_msg += _field_string(3, "1.0")
    model_msg += _field_varint(5, 1)
    model_msg += _field_string(6, "SIFMA Multimodal Phytopathological & Nutritional Neural Network")
    model_msg += _field_bytes(7, bytes(graph_msg))
    model_msg += _field_bytes(8, opset_msg)

    with open(model_path, "wb") as f:
        f.write(model_msg)

    return model_path
