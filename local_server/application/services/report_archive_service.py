# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.config import config as app_settings
from core.logger import logger


class ReportArchiveService:
    """
    Servicio para el archivo, catalogación, búsqueda y gestión de reportes y dossiers PDF
    en la carpeta predeterminada de SIFMA (%APPDATA%\\SIFMA\\data\\reports).
    """

    INDEX_FILENAME = "reports_index.json"

    @classmethod
    def get_reports_dir(cls) -> str:
        os.makedirs(app_settings.REPORTS_DIR, exist_ok=True)
        return os.path.abspath(app_settings.REPORTS_DIR)

    @classmethod
    def _get_index_path(cls) -> str:
        return os.path.join(cls.get_reports_dir(), cls.INDEX_FILENAME)

    @classmethod
    def _load_index(cls) -> Dict[str, Dict[str, Any]]:
        index_path = cls._get_index_path()
        if not os.path.exists(index_path):
            return {}
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"No se pudo leer reports_index.json: {e}")
            return {}

    @classmethod
    def _save_index(cls, index_data: Dict[str, Dict[str, Any]]) -> None:
        index_path = cls._get_index_path()
        try:
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"No se pudo guardar reports_index.json: {e}")

    @staticmethod
    def sanitize_slug(text: str) -> str:
        """Limpia un texto libre para usarlo como sufijo seguro en un nombre de archivo."""
        if not text:
            return ""
        clean = text.strip()
        clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', clean)
        clean = re.sub(r'\s+', '_', clean)
        return clean[:80]

    @classmethod
    def build_report_filename(cls, report_id: str, custom_name: str = "") -> str:
        base_id = cls.sanitize_slug(report_id) or f"SIFMA-REP-{datetime.now().strftime('%Y%m%d')}-CAN1"
        if base_id.lower().endswith(".pdf"):
            base_id = base_id[:-4]
        extra = cls.sanitize_slug(custom_name)
        if extra.lower().endswith(".pdf"):
            extra = extra[:-4]
        if extra and extra.lower() != base_id.lower():
            return f"{base_id}_{extra}.pdf"
        return f"{base_id}.pdf"

    @classmethod
    def extract_meta_from_filename(cls, filename: str) -> Dict[str, Any]:
        """Infiere fecha, report_id y nombre adicional si un PDF fue copiado manualmente a la carpeta."""
        stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
        report_id = stem
        target_date = ""
        plant_id = 1
        custom_name = ""

        match = re.match(r"^(SIFMA-REP-(\d{4})(\d{2})(\d{2})-CAN(\d+))(?:[_\-\s]+(.*))?$", stem, re.IGNORECASE)
        if match:
            report_id = match.group(1).upper()
            target_date = f"{match.group(2)}-{match.group(3)}-{match.group(4)}"
            plant_id = int(match.group(5))
            raw_extra = (match.group(6) or "").replace("_", " ").strip()
            custom_name = raw_extra
        else:
            date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})|(\d{4})(\d{2})(\d{2})", stem)
            if date_match:
                g = date_match.groups()
                if g[0]:
                    target_date = f"{g[0]}-{g[1]}-{g[2]}"
                else:
                    target_date = f"{g[3]}-{g[4]}-{g[5]}"
            custom_name = stem.replace("_", " ")

        return {
            "report_id": report_id,
            "target_date": target_date,
            "plant_id": plant_id,
            "custom_name": custom_name,
        }

    @classmethod
    def register_saved_pdf(
        cls,
        filename: str,
        report_id: str = "",
        custom_name: str = "",
        target_date: str = "",
        plant_id: int = 1,
        crop_name: str = "",
        author: str = "",
    ) -> Dict[str, Any]:
        """Registra o actualiza los metadatos de un archivo PDF guardado en la carpeta de reportes."""
        reports_dir = cls.get_reports_dir()
        full_path = os.path.join(reports_dir, filename)
        inferred = cls.extract_meta_from_filename(filename)

        index_data = cls._load_index()
        size_bytes = os.path.getsize(full_path) if os.path.exists(full_path) else 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "filename": filename,
            "report_id": report_id or inferred["report_id"],
            "custom_name": custom_name.strip() if custom_name else inferred["custom_name"],
            "target_date": target_date or inferred["target_date"] or datetime.now().strftime("%Y-%m-%d"),
            "plant_id": int(plant_id or inferred["plant_id"] or 1),
            "crop_name": crop_name or "Cebollín",
            "author": author or "Administrador SIFMA",
            "created_at": now_str,
            "size_kb": round(size_bytes / 1024.0, 1),
            "url": f"/static/data/reports/{filename}",
        }
        index_data[filename] = entry
        cls._save_index(index_data)
        return entry

    @classmethod
    def list_reports(cls, query: str = "", date_filter: str = "") -> List[Dict[str, Any]]:
        """
        Escanea la carpeta de reportes PDF, sincroniza el índice con los archivos reales en disco
        y filtra por texto (ID, nombre personalizado, especie, fecha) o fecha exacta.
        """
        reports_dir = cls.get_reports_dir()
        index_data = cls._load_index()
        updated_index = {}
        results = []

        try:
            files = [
                f for f in os.listdir(reports_dir)
                if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(reports_dir, f))
            ]
        except Exception:
            files = []

        for fname in files:
            fpath = os.path.join(reports_dir, fname)
            try:
                stat = os.stat(fpath)
                mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size_kb = round(stat.st_size / 1024.0, 1)
            except Exception:
                mtime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                size_kb = 0.0

            meta = index_data.get(fname)
            if not meta:
                inferred = cls.extract_meta_from_filename(fname)
                meta = {
                    "filename": fname,
                    "report_id": inferred["report_id"],
                    "custom_name": inferred["custom_name"],
                    "target_date": inferred["target_date"] or mtime_str[:10],
                    "plant_id": inferred["plant_id"],
                    "crop_name": "Ecosistema Principal",
                    "author": "Administrador SIFMA",
                    "created_at": mtime_str,
                    "size_kb": size_kb,
                }
            else:
                meta["filename"] = fname
                meta["size_kb"] = size_kb
                if not meta.get("created_at"):
                    meta["created_at"] = mtime_str

            meta["url"] = f"/static/data/reports/{fname}"
            meta["full_path"] = fpath
            updated_index[fname] = meta
            results.append(meta)

        if len(updated_index) != len(index_data):
            cls._save_index(updated_index)

        # Ordenar del más reciente al más antiguo
        results.sort(key=lambda x: (x.get("created_at", ""), x.get("target_date", "")), reverse=True)

        q = (query or "").strip().lower()
        df = (date_filter or "").strip()

        if q or df:
            filtered = []
            for r in results:
                if df and r.get("target_date") != df and df not in r.get("created_at", ""):
                    continue
                if q:
                    searchable = " ".join([
                        str(r.get("filename", "")),
                        str(r.get("report_id", "")),
                        str(r.get("custom_name", "")),
                        str(r.get("target_date", "")),
                        str(r.get("crop_name", "")),
                        str(r.get("author", "")),
                    ]).lower()
                    if q not in searchable:
                        continue
                filtered.append(r)
            return filtered

        return results

    @classmethod
    def rename_report(cls, filename: str, new_custom_name: str) -> Optional[Dict[str, Any]]:
        """Actualiza la etiqueta/nombre adicional de un PDF y renombra el archivo conservando su INFORME ID."""
        reports_dir = cls.get_reports_dir()
        safe_fname = os.path.basename(filename)
        old_path = os.path.join(reports_dir, safe_fname)
        if not os.path.exists(old_path):
            return None

        index_data = cls._load_index()
        meta = index_data.get(safe_fname) or cls.extract_meta_from_filename(safe_fname)
        report_id = meta.get("report_id") or cls.extract_meta_from_filename(safe_fname)["report_id"]

        new_filename = cls.build_report_filename(report_id, new_custom_name)
        new_path = os.path.join(reports_dir, new_filename)

        if os.path.abspath(old_path) != os.path.abspath(new_path):
            if os.path.exists(new_path):
                os.remove(new_path)
            shutil.move(old_path, new_path)
            index_data.pop(safe_fname, None)

        entry = cls.register_saved_pdf(
            filename=new_filename,
            report_id=report_id,
            custom_name=new_custom_name,
            target_date=meta.get("target_date", ""),
            plant_id=meta.get("plant_id", 1),
            crop_name=meta.get("crop_name", ""),
            author=meta.get("author", ""),
        )
        return entry

    @classmethod
    def delete_report(cls, filename: str) -> bool:
        reports_dir = cls.get_reports_dir()
        safe_fname = os.path.basename(filename)
        fpath = os.path.join(reports_dir, safe_fname)
        if not os.path.exists(fpath):
            return False
        try:
            os.remove(fpath)
            index_data = cls._load_index()
            if safe_fname in index_data:
                index_data.pop(safe_fname, None)
                cls._save_index(index_data)
            return True
        except Exception as e:
            logger.error(f"Error eliminando reporte PDF {safe_fname}: {e}")
            return False

    @classmethod
    def open_reports_folder_in_explorer(cls) -> bool:
        reports_dir = cls.get_reports_dir()
        try:
            if os.name == "nt":
                os.startfile(reports_dir)
            else:
                subprocess.Popen(["xdg-open", reports_dir])
            return True
        except Exception as e:
            logger.warning(f"No se pudo abrir la carpeta de reportes: {e}")
            return False

    @classmethod
    def export_current_webview_to_pdf(cls, output_pdf_path: str) -> bool:
        """
        En modo escritorio (PyWebView + EdgeChromium WebView2), invoca CoreWebView2.PrintToPdfAsync
        para guardar directamente el reporte actual en PDF sin cuadro de diálogo manual.
        """
        try:
            import webview
            if not webview.windows:
                return False
            win = webview.windows[0]
            native_form = getattr(win, "native", None)
            if not native_form:
                return False
            wv2_ctrl = getattr(native_form, "webview", None)
            if not wv2_ctrl or not getattr(wv2_ctrl, "CoreWebView2", None):
                return False

            from threading import Semaphore
            from System import Func, Object, Action, Boolean
            from System.Threading.Tasks import Task

            done = Semaphore(0)
            result_box = {"ok": False}

            def _on_pdf_finished(task):
                try:
                    result_box["ok"] = bool(task.Result)
                except Exception as ex:
                    logger.warning(f"Error en tarea PrintToPdfAsync: {ex}")
                    result_box["ok"] = False
                finally:
                    done.release()

            def _invoke_print():
                try:
                    core_wv = wv2_ctrl.CoreWebView2
                    settings = core_wv.Environment.CreatePrintSettings()
                    settings.ShouldPrintBackgrounds = True
                    settings.ShouldPrintHeaderAndFooter = False
                    # Márgenes suaves en pulgadas (~0.4 in = 10mm)
                    settings.MarginTop = 0.4
                    settings.MarginBottom = 0.4
                    settings.MarginLeft = 0.4
                    settings.MarginRight = 0.4
                    task = core_wv.PrintToPdfAsync(output_pdf_path, settings)
                    task.ContinueWith(Action[Task[Boolean]](_on_pdf_finished))
                except Exception as ex:
                    logger.warning(f"Fallo invocando PrintToPdfAsync en hilo UI: {ex}")
                    done.release()

            wv2_ctrl.Invoke(Func[Object](_invoke_print))
            done.acquire()
            return result_box["ok"] and os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 0
        except Exception as e:
            logger.warning(f"Exportación directa WebView2 PDF no disponible: {e}")
            return False

