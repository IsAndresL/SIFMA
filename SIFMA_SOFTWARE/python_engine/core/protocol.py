# SIFMA — Protocolo IPC JSON-RPC para Python Sidecar
# Facilita el intercambio desacoplado de comandos entre Rust (Tauri) y Python.

import json
from typing import Dict, Any, Optional

class JsonRpcProtocol:
    @staticmethod
    def parse_request(raw_line: str) -> Dict[str, Any]:
        """Parsea y valida una solicitud JSON-RPC 2.0 proveniente de stdin."""
        try:
            req = json.loads(raw_line.strip())
            if not isinstance(req, dict):
                raise ValueError("Payload debe ser un objeto JSON")
            if "id" not in req or "method" not in req:
                raise ValueError("Faltan campos obligatorios: id, method")
            return req
        except Exception as e:
            raise ValueError(f"JSON inválido o malformado: {str(e)}")

    @staticmethod
    def format_success(req_id: Any, result: Any) -> str:
        """Formatea una respuesta exitosa compatible con JSON-RPC 2.0."""
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
            "error": None
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def format_error(req_id: Optional[Any], code: int, message: str) -> str:
        """Formatea una respuesta de error compatible con JSON-RPC 2.0."""
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": None,
            "error": {
                "code": code,
                "message": message
            }
        }
        return json.dumps(payload, ensure_ascii=False)

