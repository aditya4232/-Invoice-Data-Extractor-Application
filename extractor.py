"""
India-Specific Field Extraction Module for Invoice Data Extractor.

Extracts structured data from Indian invoice OCR text using regex and rule-based NLP.
Focused on Indian GST Tax Invoice fields: GSTIN, PAN, GST amounts (CGST/SGST/IGST),
Indian date formats (DD/MM/YYYY), Indian currency (₹, INR, Rs.),
and Indian company naming conventions (Pvt Ltd, LLP, Ltd, etc.).
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FieldExtractor:
    """Extracts Indian invoice fields from raw OCR text using regex and rules."""

    GSTIN_PATTERN = r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1]"
    PAN_PATTERN = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"

    def __init__(self):
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> Dict[str, List[str]]:
        return {
            "gstin": [
                r"(?i)(?:gstin|gst\s*(?:no|number|id|identification|registration))[\s]*[:\-#.]*\s*("
                + self.GSTIN_PATTERN
                + r")",
                r"(?i)(?:gstin|gst\s*no)[\s]*[:=\-]+\s*(" + self.GSTIN_PATTERN + r")",
                r"\b(" + self.GSTIN_PATTERN.replace(" ", "") + r")\b",
                r"([0-9]{2}\s*[A-Z]{5}\s*[0-9]{4}\s*[A-Z]{1}\s*[1-9A-Z]{1}\s*Z\s*[0-9A-Z]{1})",
            ],
            "pan": [
                r"(?i)(?:pan|permanent\s*account\s*number)[\s]*[:\-#.]*\s*("
                + self.PAN_PATTERN
                + r")",
                r"(?i)(?:pan|p\.a\.n\.)[\s]*[:=\-]+\s*(" + self.PAN_PATTERN + r")",
                r"\b(" + self.PAN_PATTERN + r")\b",
            ],
            "vendor_name": [
                r"(?i)(?:sold\s*by|seller|vendor|supplier|from|billed\s*by|consignor)[\s]*[:\-#.]*\s*\n?\s*([A-Za-z][A-Za-z\s&.,\-]{1,80}?)(?:\n|$)",
                r"(?i)(?:company\s*name|firm\s*name|name\s*of\s*the\s*seller)[\s]*[:\-#.]*\s*([A-Za-z][A-Za-z\s&.,\-]{1,80}?)(?:\n|$)",
                r"(?:^|\n)\s*([A-Z][A-Za-z\s]+(?:Pvt\.?\s*Ltd\.?|Ltd\.?|LLP|Private\s*Limited|Limited|Inc\.?|Corp\.?))\s*(?:\n|$)",
                r"(?:^|\n)\s*([A-Z][A-Za-z\s&]+(?:Pvt\.?\s*Ltd\.?|Ltd\.?|LLP|Limited))\s*(?:\n|,|\.|$)",
                r"(?i)(?:name|company|supplier|vendor)[\s]*[:\-]*\s*([A-Za-z][A-Za-z\s&.,\-]{2,60})",
                r"(?:^|\n)\s{0,5}([A-Z][A-Za-z0-9\s&.,\-]{3,60})(?:\n|GSTIN|\s+[0-9])",
                r"(?:^|\n)\s*([A-Za-z][A-Za-z\s&.,\-]{3,50})\s+(?:Pvt|Ltd|Inc|Corp|GSTIN)",
            ],
            "invoice_number": [
                r"(?i)(?:invoice|inv|bill|tax\s*invoice)[\s]*(?:no|number|#|num|id)[.:;\-\s]*([A-Za-z0-9][\w\-/\.]{2,25})",
                r"(?i)(?:invoice|inv)[\s]*[:\-#.]+\s*([A-Za-z0-9][\w\-/\.]{2,25})",
                r"(?i)(?:bill\s*no|ref\s*no|ref)[.:;\-\s]*([A-Za-z0-9][\w\-/\.]{2,25})",
                r"(?i)(?:ref)[.:;\-\s]*(CI[\-][A-Za-z0-9][\w\-/]{2,25})",
                r"\b([A-Z]{2,4}[-/]\d{4}[-/]?\d{1,5})\b",
                r"\b(INV[-/]\d{1,10})\b",
                r"\b(INV/\d{4}/\w{1,5}/\d{1,10})\b",
            ],
            "invoice_date": [
                r"(?i)(?:invoice|bill|tax)\s*(?:date|dated)[.:;\-\s]*(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
                r"(?i)(?:date|dated|dt)[.:;\-\s]*(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
                r"(?i)(?:invoice|bill)\s*(?:date)[.:;\-\s]*(\d{1,2}\s+\w{3,9}\s+\d{2,4})",
                r"(?i)(?:date)[.:;\-\s]*(\d{4}[\-/]\d{1,2}[\-/]\d{1,2})",
                r"(?i)(?:dated)[.:;\-\s]*(\d{1,2}[\-/]\d{1,2}[\-/]\d{4})",
                r"(?:invoice|date|dated)[\s#:]*(\d{1,2}[\-.]\d{1,2}[\-.]\d{2,4})",
                r"(\d{1,2}[\s/]\w{3,9}[\s]\d{2,4})",
                r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            ],
            "due_date": [
                r"(?i)(?:due|payment|pay)[\s]*(?:date|by|on)[.:;\-\s]*(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
                r"(?i)(?:due)[.:;\-\s]*(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
                r"(?i)(?:payment\s*terms)[\s:]*(?:net\s*\d+|(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}))",
            ],
            "total_amount": [
                r"(?i)(?:grand\s*total|net\s*total|total\s*amount|invoice\s*total|amount\s*payable|amount\s*due|balance\s*due|net\s*amount)[\s:]*[₹]?\s*(?:INR\s*)?(?:Rs\.?\s*)?([\d,]+\.?\d*)",
                r"(?i)(?:grand\s*total|net\s*total|total\s*amount|invoice\s*total|amount\s*payable|amount\s*due)[\s:]*[₹]?\s*(?:INR\s*)?(?:Rs\.?\s*)?([\d,]+\.?\d*)",
                r"(?i)(?:grand\s*total|net\s*total|total\s*amount|invoice\s*total|amount\s*payable|amount\s*due)[\s:]*[₹]?\s*([\d,]+\.?\d*)",
                r"(?i)(?:total)[\s:]*[₹]?\s*([\d,]+\.?\d*)",
                r"[₹]\s*([\d,]+\.?\d{2})\s*(?:\n|$)",
                r"(?:total|amount)[\s:]*([\d,]+\.?\d{2})(?:\s|$|\n)",
                r"(?:^|\n)\s*(?:Rs\.?|₹|INR)?\s*([\d,]+\.?\d{2})\s*(?:\n|Total|Amount|$)",
            ],
            "cgst_amount": [
                r"(?i)(?:cgst|central\s*gst|c\.gst)[\s]*(?:@?\s*[\d.]+%?)?[\s]*[:\-#.]*\s*[₹\s]*([\d,]+\.?\d*)",
            ],
            "sgst_amount": [
                r"(?i)(?:sgst|state\s*gst|s\.gst)[\s]*(?:@?\s*[\d.]+%?)?[\s]*[:\-#.]*\s*[₹\s]*([\d,]+\.?\d*)",
            ],
            "igst_amount": [
                r"(?i)(?:igst|integrated\s*gst|i\.gst)[\s]*(?:@?\s*[\d.]+%?)?[\s]*[:\-#.]*\s*[₹\s]*([\d,]+\.?\d*)",
            ],
            "po_number": [
                r"(?i)(?:po|purchase\s*order|p\.o\.|po\s*no)[\s]*(?:no|number|#|ref)?[.:;\-\s]*([A-Za-z0-9][\w\-/]{4,25})",
                r"(?i)(?:po|purchase\s*order)[\s]*[:\-#.]+\s*([A-Za-z0-9][\w\-/]{4,25})",
                r"(?i)(?:po\s*no|po\s*number)[\s]*[:=\-]*\s*([A-Z0-9]{4,20})",
            ],
            "place_of_supply": [
                r"(?i)(?:place\s*of\s*supply)[\s]*[:\-#.]*\s*([A-Za-z][A-Za-z\s,\-]{2,40}?)(?:\n|$)",
            ],
            "hsn_sac": [
                r"(?i)(?:hsn|sac|hsn/sac)[\s]*(?:code|no)?[.:;\-\s]*([\d]{4,8})",
                r"\b(\d{4,8})\b(?=\s*[\d,]+\.\d{2})",
            ],
        }

    def extract_all_fields(self, text: str) -> Dict[str, object]:
        if not text or not text.strip():
            logger.warning("Empty text provided for field extraction")
            return self._empty_result()

        text = self._preprocess_text(text)

        result = {}
        confidence_details = {}

        # Extract each field with confidence tracking
        for field_name in [
            "gstin",
            "pan",
            "vendor_name",
            "invoice_number",
            "invoice_date",
            "due_date",
            "total_amount",
            "cgst_amount",
            "sgst_amount",
            "igst_amount",
            "po_number",
            "place_of_supply",
        ]:
            value, pattern_idx, pattern_preview = self._find_match(
                text, self.patterns[field_name], field_name
            )

            if value:
                if field_name in ["gstin", "pan"]:
                    result[field_name] = value.upper()
                else:
                    result[field_name] = value
                confidence = self._calculate_field_confidence(
                    value, pattern_idx, text, field_name
                )
                confidence_details[field_name] = {
                    "confidence": round(confidence, 1),
                    "pattern_index": pattern_idx,
                    "pattern_preview": pattern_preview + "...",
                }
            else:
                result[field_name] = "Not Found"
                confidence_details[field_name] = {
                    "confidence": 0.0,
                    "pattern_index": -1,
                    "pattern_preview": "No match found",
                }

        # Derive PAN from GSTIN if not found
        if result.get("gstin") != "Not Found" and result["pan"] == "Not Found":
            result["pan"] = self._derive_pan_from_gstin(result["gstin"])
            if result["pan"] != "Not Found":
                confidence_details["pan"] = {
                    "confidence": 60.0,
                    "pattern_index": -1,
                    "pattern_preview": "Derived from GSTIN",
                }

        # Extract all amounts
        result["all_amounts"] = self.extract_all_amounts(text)

        # Store confidence details
        result["_confidence_details"] = confidence_details

        return result

    def _empty_result(self) -> Dict[str, object]:
        return {
            "vendor_name": "Not Found",
            "invoice_number": "Not Found",
            "invoice_date": "Not Found",
            "due_date": "Not Found",
            "total_amount": "Not Found",
            "gstin": "Not Found",
            "pan": "Not Found",
            "cgst_amount": "Not Found",
            "sgst_amount": "Not Found",
            "igst_amount": "Not Found",
            "po_number": "Not Found",
            "place_of_supply": "Not Found",
            "all_amounts": [],
        }

    def _preprocess_text(self, text: str) -> str:
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text.strip()

    def _find_match(
        self, text: str, patterns: List[str], field_name: str
    ) -> tuple[Optional[str], int, str]:
        """Find match with confidence and pattern tracking.

        Returns: (value, pattern_index, pattern_preview)
        """
        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                try:
                    raw = match.group(1)
                    if raw is None:
                        continue
                    value = raw.strip()
                except (AttributeError, IndexError):
                    continue
                value = re.sub(r"\s+", " ", value)
                value = value.rstrip(".,;:")
                if value:
                    pattern_preview = pattern[:80].replace("\n", " ")
                    logger.debug(
                        f"Found {field_name}: {value} (pattern idx: {idx}, pattern: {pattern_preview}...)"
                    )
                    return value, idx, pattern_preview
        logger.debug(f"Could not find {field_name}")
        return None, -1, ""

    def _calculate_field_confidence(
        self, value: Optional[str], pattern_idx: int, text: str, field_name: str
    ) -> float:
        """Calculate confidence score for a field extraction."""
        if not value or value == "Not Found":
            return 0.0

        confidence = 70.0

        # Pattern position bonus (earlier patterns are usually more specific)
        if pattern_idx == 0:
            confidence += 15.0
        elif pattern_idx == 1:
            confidence += 10.0
        elif pattern_idx < 4:
            confidence += 5.0

        # Value quality checks
        if field_name == "gstin":
            if len(value) == 15 and re.match(self.GSTIN_PATTERN, value, re.IGNORECASE):
                confidence += 10.0
            else:
                confidence -= 20.0
        elif field_name == "pan":
            if len(value) == 10 and re.match(self.PAN_PATTERN, value, re.IGNORECASE):
                confidence += 10.0
            else:
                confidence -= 20.0
        elif field_name == "total_amount":
            try:
                amount = float(value.replace(",", ""))
                if amount > 0:
                    confidence += 10.0
                if amount > 1000000:
                    confidence -= 5.0
            except (ValueError, TypeError):
                confidence -= 30.0
        elif field_name in ["invoice_date", "due_date"]:
            try:
                from dateutil import parser as date_parser

                date_parser.parse(value, dayfirst=True)
                confidence += 10.0
            except (ValueError, TypeError):
                confidence -= 20.0
        elif field_name == "vendor_name":
            if 3 < len(value) < 100:
                confidence += 10.0
            if re.search(r"(Pvt|Ltd|LLP|Inc|Corp)", value, re.IGNORECASE):
                confidence += 5.0

        # Text context bonus
        if field_name in text[:500]:
            confidence += 5.0

        return max(0.0, min(100.0, confidence))

    def extract_gstin(self, text: str) -> str:
        result, _, _ = self._find_match(text, self.patterns["gstin"], "gstin")
        if result:
            return result.upper()
        return "Not Found"

    def extract_pan(self, text: str) -> str:
        result, _, _ = self._find_match(text, self.patterns["pan"], "pan")
        if result:
            return result.upper()
        return "Not Found"

    def _derive_pan_from_gstin(self, gstin: str) -> str:
        if len(gstin) == 15:
            possible_pan = gstin[2:12]
            if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", possible_pan):
                return possible_pan
        return "Not Found"

    def extract_vendor_name(self, text: str) -> str:
        result, _, _ = self._find_match(
            text, self.patterns["vendor_name"], "vendor_name"
        )
        if result:
            result = re.sub(r"\s+", " ", result).strip()
            result = re.sub(r"\s*[|\-]\s*$", "", result)
            for suffix in [
                " GSTIN",
                " GST No",
                " PAN",
                " State",
                " Phone",
                " Email",
                " Tel",
                " Fax",
                " Mobile",
                " Web",
            ]:
                if suffix in result:
                    result = result[: result.index(suffix)]
            if len(result) > 80:
                result = result[:80]
            if result.strip():
                return result.strip()
        lines = text.split("\n")
        for line in lines[:8]:
            line = line.strip()
            if re.search(
                r"(?:Pvt\.?\s*Ltd\.?|Ltd\.?|LLP|Private\s*Limited|Limited|Inc\.?|Corp\.?)",
                line,
                re.IGNORECASE,
            ):
                clean = re.sub(r"[\d]", "", line).strip()
                if len(clean) > 3 and len(clean) < 80:
                    return clean
        return "Not Found"

    def extract_invoice_number(self, str_text: str) -> str:
        result, _, _ = self._find_match(
            str_text, self.patterns["invoice_number"], "invoice_number"
        )
        if result:
            clean = result.strip(".")
            if len(clean) >= 2:
                return clean
        lines = str_text.split("\n")
        for i, line in enumerate(lines):
            if re.search(r"(?i)(?:invoice|inv|bill|tax\s*invoice)", line):
                for j in range(max(0, i - 1), min(len(lines), i + 3)):
                    match = re.search(r"[A-Z]{2,4}[-/]\d{2,6}[-/]?\d{0,5}", lines[j])
                    if match:
                        return match.group(0)
                    match = re.search(r"[A-Z]{2,}/\d{4}/\w{1,5}/\d{1,10}", lines[j])
                    if match:
                        return match.group(0)
        return "Not Found"

    def extract_invoice_date(self, text: str) -> str:
        result, _, _ = self._find_match(
            text, self.patterns["invoice_date"], "invoice_date"
        )
        if result:
            normalized = self._normalize_date(result)
            if normalized:
                return normalized
            return result
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if re.search(r"(?i)(?:date|dated)", line):
                date_match = re.search(r"(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})", line)
                if date_match:
                    normalized = self._normalize_date(date_match.group(1))
                    if normalized:
                        return normalized
        return "Not Found"

    def extract_due_date(self, text: str) -> str:
        result, _, _ = self._find_match(text, self.patterns["due_date"], "due_date")
        if result:
            normalized = self._normalize_date(result)
            if normalized:
                return normalized
            return result
        if re.search(r"(?i)(?:net\s*30|payment\s*terms[\s:]*(?:net\s*)?30)", text):
            inv_date = self.extract_invoice_date(text)
            if inv_date != "Not Found":
                from dateutil.relativedelta import relativedelta

                try:
                    from datetime import datetime

                    dt = datetime.strptime(inv_date, "%Y-%m-%d")
                    return (dt + relativedelta(days=30)).strftime("%Y-%m-%d")
                except Exception:
                    pass
        return "Not Found"

    def extract_total_amount(self, text: str) -> str:
        result, _, _ = self._find_match(
            text, self.patterns["total_amount"], "total_amount"
        )
        if result:
            return result
        amounts = self.extract_all_amounts(text)
        if amounts:
            float_amounts = []
            for a in amounts:
                try:
                    val = float(
                        str(a)
                        .replace(",", "")
                        .replace("₹", "")
                        .replace("INR", "")
                        .replace("Rs.", "")
                        .replace("Rs", "")
                        .strip()
                    )
                    float_amounts.append((a, val))
                except (ValueError, TypeError):
                    continue
            if float_amounts:
                float_amounts.sort(key=lambda x: x[1], reverse=True)
                return float_amounts[0][0]
        return "Not Found"

    def extract_cgst(self, text: str) -> str:
        result, _, _ = self._find_match(
            text, self.patterns["cgst_amount"], "cgst_amount"
        )
        return result if result else "Not Found"

    def extract_sgst(self, text: str) -> str:
        result, _, _ = self._find_match(
            text, self.patterns["sgst_amount"], "sgst_amount"
        )
        return result if result else "Not Found"

    def extract_igst(self, text: str) -> str:
        result, _, _ = self._find_match(
            text, self.patterns["igst_amount"], "igst_amount"
        )
        return result if result else "Not Found"

    def extract_po_number(self, text: str) -> str:
        result, _, _ = self._find_match(text, self.patterns["po_number"], "po_number")
        if result:
            return result
        return "Not Found"

    def extract_place_of_supply(self, text: str) -> str:
        result, _, _ = self._find_match(
            text, self.patterns["place_of_supply"], "place_of_supply"
        )
        if result:
            return result
        return "Not Found"

    def extract_all_amounts(self, text: str) -> List[str]:
        amount_patterns = [
            r"[₹]\s*([\d,]+\.?\d*)",
            r"(?:INR|Rs\.?)\s*([\d,]+\.?\d*)",
            r"([\d,]+\.?\d*)\s*(?:INR|Rs\.?)",
        ]
        amounts = []
        seen = set()
        for pattern in amount_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                value = match.group(1).strip()
                cleaned = self._parse_amount_value(value)
                if cleaned and cleaned > 0 and value not in seen:
                    seen.add(value)
                    amounts.append(value)
        amounts.sort(key=lambda x: self._parse_amount_value(x) or 0, reverse=True)
        return amounts

    def _normalize_date(self, date_str: str) -> Optional[str]:
        date_str = date_str.strip().rstrip(".,;:")
        date_str = re.sub(r"[\\]", "/", date_str)
        try:
            from dateutil import parser as date_parser

            dt = date_parser.parse(date_str, dayfirst=True)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
        patterns = [
            (r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", "dmy"),
            (r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$", "ymd"),
            (r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{2})$", "dmy_short"),
            (r"^(\d{1,2})\s+(\w{3,9})\s+(\d{2,4})$", "dmy_text"),
        ]
        for pattern, fmt in patterns:
            match = re.match(pattern, date_str, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    if fmt == "ymd":
                        y, m, d = int(groups[0]), int(groups[1]), int(groups[2])
                    elif fmt == "dmy":
                        d, m, y = int(groups[0]), int(groups[1]), int(groups[2])
                    elif fmt == "dmy_short":
                        d, m, y = int(groups[0]), int(groups[1]), int(groups[2])
                        y += 2000 if y < 100 else 0
                    elif fmt == "dmy_text":
                        d = int(groups[0])
                        month_map = {
                            "jan": 1,
                            "feb": 2,
                            "mar": 3,
                            "apr": 4,
                            "may": 5,
                            "jun": 6,
                            "jul": 7,
                            "aug": 8,
                            "sep": 9,
                            "oct": 10,
                            "nov": 11,
                            "dec": 12,
                            "january": 1,
                            "february": 2,
                            "march": 3,
                            "april": 4,
                            "june": 6,
                            "july": 7,
                            "august": 8,
                            "september": 9,
                            "october": 10,
                            "november": 11,
                            "december": 12,
                        }
                        m = month_map.get(groups[1].lower(), 1)
                        y = int(groups[2])
                        y += 2000 if y < 100 else 0
                    else:
                        continue
                    if 1 <= m <= 12 and 1 <= d <= 31 and y >= 1900:
                        return f"{y:04d}-{m:02d}-{d:02d}"
                except (ValueError, IndexError):
                    continue
        return None

    def _parse_amount_value(self, amount_str: str) -> Optional[float]:
        try:
            cleaned = (
                amount_str.replace("₹", "")
                .replace("INR", "")
                .replace("Rs.", "")
                .replace("Rs", "")
            )
            cleaned = cleaned.replace(",", "").strip()
            cleaned = re.sub(r"[^\d.\-]", "", cleaned)
            if not cleaned:
                return None
            value = float(cleaned)
            return value if value > 0 else None
        except (ValueError, TypeError):
            return None
