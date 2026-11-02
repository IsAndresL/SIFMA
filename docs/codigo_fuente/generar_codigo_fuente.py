# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

"""
Script de consolidación de código fuente para depósito ante la DNDA.
Genera SIFMA_codigo_fuente_completo.txt y SIFMA_codigo_fuente_completo.pdf
"""

import os
import sys
import subprocess
import html

TARGET_EXTENSIONS = ('.py', '.js', '.html', '.css', '.bat', '.ps1', '.sh')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTPUT_DIR = os.path.abspath(os.path.dirname(__file__))

def get_source_files():
    files_list = []
    scan_dirs = ['local_server', 'raspi_node', 'instalacion']
    
    for sdir in scan_dirs:
        full_sdir = os.path.join(ROOT_DIR, sdir)
        if not os.path.exists(full_sdir):
            continue
        for root, dirs, files in os.walk(full_sdir):
            if any(x in root for x in ('.git', '.venv', '__pycache__', 'scratch', 'temp_chrome_profile', 'uploads', 'processed', 'telemetry', 'data')):
                continue
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                if ext in TARGET_EXTENSIONS:
                    files_list.append(os.path.join(root, f))
                    
    return sorted(files_list)

def generate_txt(source_files, output_txt_path):
    total_lines = 0
    file_stats = []
    
    for fpath in source_files:
        rel_path = os.path.relpath(fpath, ROOT_DIR).replace('\\', '/')
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(fpath, 'r', encoding='cp1252', errors='ignore') as f:
                lines = f.readlines()
        file_stats.append((rel_path, len(lines), lines))
        total_lines += len(lines)
        
    print(f"Total source files to consolidate: {len(file_stats)}")
    print(f"Total lines of source code: {total_lines}")
    
    with open(output_txt_path, 'w', encoding='utf-8', newline='\n') as out:
        out.write("================================================================================\n")
        out.write("SIFMA — SISTEMA INTEGRAL DE FENOTIPADO Y MONITOREO AGRÍCOLA\n")
        out.write("CÓDIGO FUENTE COMPLETO PARA DEPÓSITO LEGAL ANTE LA DNDA (COLOMBIA)\n")
        out.write("================================================================================\n")
        out.write("Versión de Software: 1.0.0\n")
        out.write("Año de Creación: 2026\n")
        out.write("Autores (Desarrolladores del Código): Andrés Felipe Luna Camargo y Cristian David Peña Martínez\n")
        out.write("Titular de Derechos Patrimoniales: [POR DEFINIR] (Pendiente formalización con Universidad del Magdalena)\n")
        out.write(f"Total de Archivos Consolidados: {len(file_stats)}\n")
        out.write(f"Total de Líneas de Código Fuente: {total_lines}\n")
        out.write("================================================================================\n\n")
        
        out.write("--- ÍNDICE DE ARCHIVOS CONSOLIDADOS ---\n\n")
        for idx, (rpath, count, _) in enumerate(file_stats, 1):
            out.write(f"{idx:3d}. {rpath:<65} [{count:5d} líneas]\n")
        out.write("\n" + "="*80 + "\n\n")
        
        for idx, (rpath, count, lines) in enumerate(file_stats, 1):
            out.write("="*80 + "\n")
            out.write(f"ARCHIVO {idx:3d}/{len(file_stats)}: {rpath} ({count} líneas)\n")
            out.write("="*80 + "\n")
            for lno, line in enumerate(lines, 1):
                clean_line = line.rstrip('\r\n')
                out.write(f"{lno:5d} | {clean_line}\n")
            out.write("\n\n")
            
    print(f"Saved: {output_txt_path} ({os.path.getsize(output_txt_path)} bytes)")
    return file_stats

def generate_pdf(file_stats, output_pdf_path):
    html_temp_path = os.path.join(OUTPUT_DIR, '_temp_source_render.html')
    
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='es'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<title>SIFMA - Código Fuente Completo - DNDA</title>",
        "<style>",
        "@page {",
        "  size: letter portrait;",
        "  margin: 18mm 14mm 18mm 14mm;",
        "  @bottom-right { content: counter(page); font-family: monospace; font-size: 8pt; }",
        "}",
        "body {",
        "  font-family: 'JetBrains Mono', 'Courier New', Courier, monospace;",
        "  font-size: 7.5pt;",
        "  line-height: 1.25;",
        "  color: #0f172a;",
        "  margin: 0;",
        "  padding: 0;",
        "}",
        ".cover-page {",
        "  page-break-after: always;",
        "  padding-top: 60px;",
        "  text-align: center;",
        "}",
        ".cover-title {",
        "  font-size: 16pt;",
        "  font-weight: bold;",
        "  margin-bottom: 8px;",
        "}",
        ".cover-subtitle {",
        "  font-size: 11pt;",
        "  color: #334155;",
        "  margin-bottom: 24px;",
        "}",
        ".cover-box {",
        "  border: 1px solid #94a3b8;",
        "  padding: 16px 20px;",
        "  margin: 30px auto;",
        "  max-width: 500px;",
        "  text-align: left;",
        "  font-size: 9pt;",
        "}",
        ".file-header {",
        "  page-break-before: always;",
        "  background: #f1f5f9;",
        "  border: 1px solid #cbd5e1;",
        "  border-left: 4px solid #0f172a;",
        "  padding: 6px 10px;",
        "  font-weight: bold;",
        "  font-size: 8.5pt;",
        "  margin-top: 15px;",
        "  margin-bottom: 8px;",
        "}",
        ".code-container {",
        "  white-space: pre-wrap;",
        "  word-wrap: break-word;",
        "  font-family: inherit;",
        "}",
        ".code-line {",
        "  display: flex;",
        "}",
        ".line-num {",
        "  width: 38px;",
        "  color: #94a3b8;",
        "  text-align: right;",
        "  padding-right: 8px;",
        "  user-select: none;",
        "  flex-shrink: 0;",
        "}",
        ".line-code {",
        "  flex: 1;",
        "}",
        "</style>",
        "</head>",
        "<body>",
        "<div class='cover-page'>",
        "<div class='cover-title'>SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola</div>",
        "<div class='cover-subtitle'>Depósito de Código Fuente Completo ante la Dirección Nacional de Derecho de Autor (DNDA)</div>",
        "<div class='cover-box'>",
        "<strong>Identificación de la Obra:</strong> SIFMA (Soporte Lógico)<br/>",
        "<strong>Versión:</strong> 1.0.0<br/>",
        "<strong>Año de Creación:</strong> 2026<br/>",
        "<strong>País de Origen:</strong> Colombia<br/>",
        "<br/>",
        "<strong>Autores (Desarrolladores del Código):</strong><br/>",
        "• Andrés Felipe Luna Camargo<br/>",
        "• Cristian David Peña Martínez<br/>",
        "<br/>",
        "<strong>Titular de los Derechos Patrimoniales:</strong><br/>",
        "[POR DEFINIR] (Pendiente formalización con Universidad del Magdalena)<br/>",
        "<br/>",
        f"<strong>Archivos Propios Compilados:</strong> {len(file_stats)} archivos<br/>",
        f"<strong>Total de Líneas de Código:</strong> {sum(count for _, count, _ in file_stats)} líneas<br/>",
        "</div>",
        "</div>"
    ]
    
    for idx, (rpath, count, lines) in enumerate(file_stats, 1):
        html_parts.append(f"<div class='file-header'>ARCHIVO {idx}/{len(file_stats)}: {html.escape(rpath)} ({count} líneas)</div>")
        code_block = []
        for lno, line in enumerate(lines, 1):
            clean_line = html.escape(line.rstrip('\r\n'))
            code_block.append(f"{lno:5d} | {clean_line}")
        html_parts.append(f"<pre style='margin:0; padding:6px 0; font-family:inherit; font-size:7pt; line-height:1.2; white-space:pre-wrap; word-break:break-all;'>{chr(10).join(code_block)}</pre>")
        
    html_parts.append("</body></html>")
    
    with open(html_temp_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))
        
    print(f"Generated HTML intermediate representation ({os.path.getsize(html_temp_path)} bytes)")
    
    # Locate Chrome or Edge
    browser_bins = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
    ]
    
    bin_found = None
    for b in browser_bins:
        if os.path.exists(b):
            bin_found = b
            break
            
    if not bin_found:
        print("Warning: Neither Chrome nor Edge executable was found for PDF rendering.")
        return
        
    print(f"Rendering PDF with Chromium: {bin_found}...")
    cmd = [
        bin_found,
        '--headless',
        '--disable-gpu',
        '--no-pdf-header-footer',
        f'--print-to-pdf={output_pdf_path}',
        f'file:///{html_temp_path}'
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(output_pdf_path):
        print(f"Saved PDF: {output_pdf_path} ({os.path.getsize(output_pdf_path)} bytes)")
    else:
        print(f"Error rendering PDF: {res.stderr}")
        
    # Clean up temp html
    if os.path.exists(html_temp_path):
        os.remove(html_temp_path)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    source_files = get_source_files()
    
    output_txt = os.path.join(OUTPUT_DIR, 'SIFMA_codigo_fuente_completo.txt')
    output_pdf = os.path.join(OUTPUT_DIR, 'SIFMA_codigo_fuente_completo.pdf')
    
    stats = generate_txt(source_files, output_txt)
    generate_pdf(stats, output_pdf)
    print("Source code consolidation finished successfully!")

if __name__ == '__main__':
    main()
