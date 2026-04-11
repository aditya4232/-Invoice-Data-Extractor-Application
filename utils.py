"""
Processing Pipeline & Utilities for Invoice Data Extractor.

Orchestrates OCR → extraction → cleaning → validation pipeline.
Handles single and batch invoice processing, result export, and logging.
Integrates with advanced training system for continuous learning.
"""

import os
import json
import logging
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
from dotenv import load_dotenv

from ocr import OCRExtractor
from extractor import FieldExtractor
from advanced_training import ContinuousLearner

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("invoice_extractor")


class DataCleaner:
    """Validates and normalizes extracted invoice field data."""

    GSTIN_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    PAN_REGEX = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"

    def clean_field(self, key: str, value: object) -> object:
        if value is None or value == "Not Found":
            return value

        cleaners = {
            "vendor_name": self._clean_vendor_name,
            "invoice_number": self._clean_invoice_number,
            "invoice_date": self._clean_date,
            "due_date": self._clean_date,
            "total_amount": self._clean_amount,
            "gstin": self._clean_gstin,
            "pan": self._clean_pan,
            "po_number": self._clean_po_number,
            "cgst_amount": self._clean_amount,
            "sgst_amount": self._clean_amount,
            "igst_amount": self._clean_amount,
        }

        cleaner = cleaners.get(key)
        if cleaner:
            try:
                return cleaner(value)
            except Exception as e:
                logger.warning(f"Error cleaning {key}: {e}")
                return value

        return value

    def clean_all(self, fields: Dict[str, object]) -> Dict[str, object]:
        cleaned = {}
        for key, value in fields.items():
            cleaned[key] = self.clean_field(key, value)
        return cleaned

    def validate_gstin(self, gstin: str) -> bool:
        if not gstin or gstin == "Not Found":
            return False
        import re

        if not re.match(self.GSTIN_REGEX, gstin):
            return False
        return True

    def validate_pan(self, pan: str) -> bool:
        if not pan or pan == "Not Found":
            return False
        import re

        return bool(re.match(self.PAN_REGEX, pan))

    def _validate_gstin_checksum(self, gstin: str) -> bool:
        if len(gstin) != 15:
            return True
        digits = "0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
        try:
            total = 0
            for i in range(14):
                val = digits.index(gstin[i])
                factor = 1 if i % 2 == 0 else 2
                product = val * factor
                total += (product // 36) + (product % 36)
            check = (36 - (total % 36)) % 36
            return digits[check] == gstin[14]
        except (ValueError, IndexError):
            return True

    @staticmethod
    def _clean_vendor_name(value: str) -> str:
        value = str(value).strip()
        value = value.rstrip(".,;:")
        value = value.replace("\n", " ")
        value = " ".join(value.split())
        return value if value else "Not Found"

    @staticmethod
    def _clean_invoice_number(value: str) -> str:
        value = str(value).strip()
        value = value.rstrip(".,;:")
        return value if value else "Not Found"

    @staticmethod
    def _clean_date(value: str) -> str:
        value = str(value).strip()
        if value == "Not Found":
            return value
        value = value.rstrip(".,;:")
        try:
            from dateutil import parser as date_parser

            dt = date_parser.parse(value, dayfirst=True)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return value

    @staticmethod
    def _clean_amount(value) -> str:
        if isinstance(value, (int, float)):
            return str(value)
        value = str(value).strip()
        if value == "Not Found":
            return value
        value = value.replace("₹", "").replace("INR", "").replace("Rs.", "")
        value = value.replace("Rs", "").replace(",", "").strip()
        try:
            amount = float(value)
            return str(amount)
        except ValueError:
            return value

    @staticmethod
    def _clean_gstin(value: str) -> str:
        value = str(value).strip().upper().replace(" ", "")
        value = value.rstrip(".,;:")
        return value if value else "Not Found"

    @staticmethod
    def _clean_pan(value: str) -> str:
        value = str(value).strip().upper().replace(" ", "")
        value = value.rstrip(".,;:")
        return value if value else "Not Found"

    @staticmethod
    def _clean_po_number(value: str) -> str:
        value = str(value).strip()
        value = value.rstrip(".,;:")
        return value if value else "Not Found"


class InvoiceProcessor:
    """Main processing pipeline that orchestrates OCR + extraction + cleaning."""

    def __init__(self, tesseract_cmd: Optional[str] = None, enable_learning: bool = True):
        self.ocr = OCRExtractor(tesseract_cmd=tesseract_cmd)
        self.extractor = FieldExtractor()
        self.cleaner = DataCleaner()
        self.enable_learning = enable_learning
        
        if enable_learning:
            self.learner = ContinuousLearner()
        else:
            self.learner = None
            
        self._setup_logging()
        self._ensure_dirs()

    def _setup_logging(self):
        log_dir = os.getenv("LOGS_DIR", "logs")
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)

        log_file = (
            log_dir_path / f"invoice_extractor_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

    def _ensure_dirs(self):
        for dir_name in ["output", "logs", "cache", "sample_invoices"]:
            Path(dir_name).mkdir(parents=True, exist_ok=True)

    def process_invoice(self, file_path: str, preprocess: bool = True) -> Dict:
        file_path = str(Path(file_path).resolve())
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        start_time = datetime.now()
        result = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "extraction_time": None,
            "confidence": None,
            "fields": {},
            "raw_text": "",
            "success": False,
            "error": None,
        }

        try:
            logger.info(f"Processing invoice: {file_path}")

            raw_text = self.ocr.extract_text(file_path, preprocess=preprocess)
            result["raw_text"] = raw_text

            try:
                confidence = self.ocr.get_confidence(file_path)
                result["confidence"] = round(confidence, 2)
            except Exception:
                result["confidence"] = None

            fields = self.extractor.extract_all_fields(raw_text)
            cleaned_fields = self.cleaner.clean_all(fields)
            
            # Include confidence details if available
            if "_confidence_details" in fields:
                result["confidence_details"] = fields.pop("_confidence_details")
            
            result["fields"] = cleaned_fields

            result["success"] = True
            logger.info(f"Successfully processed: {file_path}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error processing {file_path}: {e}")
            raise

        finally:
            end_time = datetime.now()
            result["extraction_time"] = str(end_time - start_time)

        return result

    def add_annotation(
        self,
        file_name: str,
        raw_text: str,
        extracted_fields: Dict[str, str],
        corrected_fields: Dict[str, str],
    ):
        """Add annotation for learning."""
        if self.learner:
            self.learner.annotation_store.add_annotation(
                file_name, raw_text, extracted_fields, corrected_fields
            )
            logger.info(f"Added annotation for {file_name}")
        else:
            logger.warning("Learning is disabled")

    def train_on_annotations(self):
        """Train on all stored annotations."""
        if self.learner:
            report = self.learner.learn_from_all_annotations()
            return report
        else:
            logger.warning("Learning is disabled")
            return {}

    def get_learning_dashboard(self) -> Dict:
        """Get learning dashboard data."""
        if self.learner:
            return self.learner.get_learning_dashboard()
        return {}

    def process_batch(
        self, folder_path: str, pattern: str = "*", preprocess: bool = True
    ) -> List[Dict]:
        folder = Path(folder_path)
        if not folder.is_dir():
            raise NotADirectoryError(f"Directory not found: {folder_path}")

        supported = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".pdf"}
        files = [
            f
            for f in sorted(folder.glob(pattern))
            if f.is_file() and f.suffix.lower() in supported
        ]

        if not files:
            logger.warning(f"No supported files found in {folder_path}")
            return []

        logger.info(f"Found {len(files)} files to process in {folder_path}")

        results = []
        for i, file_path in enumerate(files, 1):
            logger.info(f"Processing {i}/{len(files)}: {file_path.name}")
            try:
                result = self.process_invoice(str(file_path), preprocess=preprocess)
                results.append(result)
            except Exception as e:
                results.append(
                    {
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "success": False,
                        "error": str(e),
                        "fields": {},
                    }
                )
                logger.error(f"Failed to process {file_path}: {e}")

        successful = sum(1 for r in results if r.get("success", False))
        logger.info(
            f"Batch complete: {successful}/{len(results)} files processed successfully"
        )

        return results

    def save_results_json(
        self, results: Union[Dict, List[Dict]], output_path: str = "output/results.json"
    ) -> str:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        def make_serializable(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            if isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            return str(obj)

        serializable = make_serializable(results)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_path}")
        return str(output_path)

    def save_results_csv(
        self, results: Union[Dict, List[Dict]], output_path: str = "output/results.csv"
    ) -> str:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(results, dict):
            results = [results]

        rows = []
        for result in results:
            row = {
                "file_name": result.get("file_name", ""),
                "success": result.get("success", False),
                "confidence": result.get("confidence", ""),
                "extraction_time": result.get("extraction_time", ""),
                "error": result.get("error", ""),
            }
            fields = result.get("fields", {})
            for key, value in fields.items():
                if isinstance(value, list):
                    row[key] = ", ".join(str(v) for v in value)
                else:
                    row[key] = value
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, encoding="utf-8")

        logger.info(f"Results saved to {output_path}")
        return str(output_path)

    def get_summary(self, results: List[Dict]) -> Dict:
        if not results:
            return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0}

        total = len(results)
        successful = sum(1 for r in results if r.get("success", False))
        failed = total - successful

        fields_found = {}
        for result in results:
            if result.get("success") and result.get("fields"):
                for key, value in result["fields"].items():
                    if value and value != "Not Found":
                        fields_found[key] = fields_found.get(key, 0) + 1

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
            "fields_found": fields_found,
        }
