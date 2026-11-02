import os
import hashlib
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTPUT_FILE = os.path.join(ROOT_DIR, 'docs', 'registro_dnda', 'SUMAS_VERIFICACION_SHA256.txt')

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

files_to_hash = [
    # Documentos principales de depósito
    'README.md',
    'local_server/requirements.txt',
    'docs/arquitectura/DOCUMENTO_TECNICO.md',
    'docs/manual_usuario/MANUAL_DE_USUARIO.md',
    'docs/codigo_fuente/SIFMA_codigo_fuente_completo.txt',
    'docs/codigo_fuente/SIFMA_codigo_fuente_completo.pdf',
    'docs/registro_dnda/LISTA_DE_VERIFICACION.md',
    'docs/registro_dnda/FICHA_FORMULARIO.md',
    'docs/registro_dnda/BORRADOR_CESION_O_AUTORIZACION.md',
    'docs/INFORME_FINAL_ENTREGA.md',
    'docs/_trabajo/inventario_inicial.md',
    'docs/_trabajo/informe_comentarios.md',
    'docs/_trabajo/inventario_limpieza.md'
]

# Agregar las 13 capturas de referencia
for i in range(1, 14):
    for f in os.listdir(os.path.join(ROOT_DIR, 'docs', '_trabajo', 'capturas_base')):
        if f.startswith(f"{i:02d}_"):
            files_to_hash.append(f"docs/_trabajo/capturas_base/{f}")

lines = [
    "================================================================================",
    "SIFMA — REGISTRO DE SUMAS CRIPTOGRÁFICAS SHA-256 (FECHA CIERTA E INTEGRIDAD)",
    "================================================================================",
    "Obra: SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola",
    "Versión: 1.0.0",
    f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "Autores: Andrés Felipe Luna Camargo y Cristian David Peña Martínez",
    "Titular de Derechos Patrimoniales: [POR DEFINIR] (Pendiente formalización con Universidad del Magdalena)",
    "Algoritmo: SHA-256 (FIPS 180-4)",
    "Finalidad: Certificación de integridad de los documentos y códigos para depósito DNDA.",
    "================================================================================",
    "",
    "HASH SHA-256                                                      | TAMAÑO (BYTES) | RUTA RELATIVA DEL ARCHIVO",
    "-" * 105
]

for rel in sorted(files_to_hash):
    full = os.path.join(ROOT_DIR, rel.replace('/', os.sep))
    if os.path.exists(full):
        h = sha256_file(full)
        sz = os.path.getsize(full)
        lines.append(f"{h}  {sz:>12d}  {rel}")
    else:
        print(f"Warning: File not found: {full}")

lines.append("")
lines.append("-" * 105)
lines.append("Fin del registro de verificación criptográfica.")

with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))

print(f"Generated SHA-256 verification sums at: {OUTPUT_FILE}")

