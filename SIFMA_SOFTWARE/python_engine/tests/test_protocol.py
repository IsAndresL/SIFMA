# SIFMA — Pruebas Unitarias del Protocolo JSON-RPC
import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.protocol import JsonRpcProtocol

class TestJsonRpcProtocol(unittest.TestCase):
    def test_parse_valid_request(self):
        raw = '{"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}'
        parsed = JsonRpcProtocol.parse_request(raw)
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["method"], "ping")

    def test_parse_invalid_json(self):
        with self.assertRaises(ValueError):
            JsonRpcProtocol.parse_request("{invalid_json:")

    def test_parse_missing_fields(self):
        with self.assertRaises(ValueError):
            JsonRpcProtocol.parse_request('{"foo": "bar"}')

    def test_format_success(self):
        resp_str = JsonRpcProtocol.format_success(1, {"val": 42})
        resp = json.loads(resp_str)
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["result"]["val"], 42)
        self.assertIsNone(resp["error"])

    def test_format_error(self):
        resp_str = JsonRpcProtocol.format_error(1, -32600, "Error de prueba")
        resp = json.loads(resp_str)
        self.assertEqual(resp["id"], 1)
        self.assertIsNone(resp["result"])
        self.assertEqual(resp["error"]["code"], -32600)

if __name__ == "__main__":
    unittest.main()
