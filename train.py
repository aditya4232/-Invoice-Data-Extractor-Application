"""
Invoice Data Extractor - Pattern Tuning & Evaluation Tool

Run extraction on invoices, compare results against ground truth,
and iteratively refine regex patterns for better accuracy.

Usage:
    python train.py                          # Run on all sample_invoices/
    python train.py --dir path/to/invoices   # Custom invoice directory
    python train.py --ground-truth gt.json   # Compare against ground truth
    python train.py --tune                   # Interactive pattern tuning mode
    python train.py --export-results         # Export results to output/
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from extractor import FieldExtractor
from ocr import OCRExtractor
from utils import InvoiceProcessor, DataCleaner

GROUND_TRUTH_FILE = "ground_truth.json"
RESULTS_DIR = "output"
SAMPLES_DIR = "sample_invoices"

FIELD_NAMES = [
    "gstin",
    "pan",
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "due_date",
    "total_amount",
    "tax_amount",
    "cgst",
    "sgst",
    "igst",
    "place_of_supply",
    "items",
]


def get_processor() -> InvoiceProcessor:
    tesseract_cmd = os.environ.get("TESSERACT_CMD", "")
    kwargs = {}
    if tesseract_cmd:
        kwargs["tesseract_cmd"] = tesseract_cmd
    return InvoiceProcessor(**kwargs)


def run_on_directory(
    directory: str, processor: InvoiceProcessor
) -> list[dict[str, Any]]:
    results = []
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"  [ERROR] Directory not found: {directory}")
        return results
    exts = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
    files = sorted(
        f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in exts
    )
    if not files:
        print(f"  [WARN] No invoice files found in {directory}")
        return results
    for fp in files:
        print(f"  Processing: {fp.name} ... ", end="", flush=True)
        try:
            result = processor.process_invoice(str(fp))
            result["file"] = fp.name
            result["status"] = "success"
            n = sum(1 for k in FIELD_NAMES if result.get(k))
            print(f"OK ({n}/{len(FIELD_NAMES)} fields)")
        except Exception as e:
            result = {"file": fp.name, "status": "error", "error": str(e)}
            print(f"ERROR: {e}")
        results.append(result)
    return results


def load_ground_truth(path: str) -> dict[str, dict]:
    gt_path = Path(path)
    if not gt_path.exists():
        print(f"  [WARN] Ground truth file not found: {path}")
        return {}
    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {item.get("file", f"invoice_{i}"): item for i, item in enumerate(data)}
    return data


def evaluate(results: list[dict], ground_truth: dict[str, dict]) -> dict[str, Any]:
    eval_results = {"per_file": {}, "summary": {}}
    field_scores: dict[str, list[float]] = {f: [] for f in FIELD_NAMES}
    total, matched, missing = 0, 0, 0
    for r in results:
        fname = r.get("file", "unknown")
        gt = ground_truth.get(fname, {})
        if not gt:
            missing += 1
            continue
        total += 1
        file_scores = {}
        for field in FIELD_NAMES:
            extracted = str(r.get(field, "")).strip()
            expected = str(gt.get(field, "")).strip()
            if not expected:
                continue
            score = (
                1.0
                if extracted.lower() == expected.lower()
                else (
                    0.5
                    if extracted.lower() in expected.lower()
                    or expected.lower() in extracted.lower()
                    else 0.0
                )
            )
            field_scores[field].append(score)
            file_scores[field] = {
                "expected": expected,
                "extracted": extracted,
                "score": score,
            }
            if score > 0:
                matched += 1
        eval_results["per_file"][fname] = file_scores
    eval_results["summary"]["total_files"] = total
    eval_results["summary"]["total_fields_evaluated"] = sum(
        len(v) for v in field_scores.values()
    )
    eval_results["summary"]["overall_accuracy"] = (
        matched / sum(len(v) for v in field_scores.values()) if field_scores else 0
    )
    for field, scores in field_scores.items():
        if scores:
            eval_results["summary"][f"{field}_accuracy"] = sum(scores) / len(scores)
    return eval_results


def export_results(results: list[dict], eval_data: dict | None = None):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(RESULTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"extraction_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    if eval_data:
        with open(out_dir / f"evaluation_{ts}.json", "w", encoding="utf-8") as f:
            json.dump(eval_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Results exported to {out_dir}/")


def interactive_tune(processor: InvoiceProcessor):
    print("\n=== Interactive Pattern Tuning Mode ===")
    print("Paste invoice text below (type END on a blank line to finish):\n")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    text = "\n".join(lines)
    if not text.strip():
        print("  No text provided. Exiting.")
        return
    extractor = FieldExtractor()
    print("\n--- Extraction Results ---\n")
    results = extractor.extract_all(text)
    for field, value in results.items():
        print(f"  {field:20s}: {value if value else '<NOT FOUND>'}")
    print("\n--- GSTIN Details ---")
    gstins = extractor.extract_gstin(text)
    for i, g in enumerate(gstins):
        print(f"  GSTIN #{i + 1}: {g}")
        pan = extractor._derive_pan_from_gstin(g)
        print(f"    -> PAN : {pan}" if pan else "    -> PAN : <cannot derive>")
    print("\n--- Tax Breakdown ---")
    for tax_type in ["cgst", "sgst", "igst"]:
        taxes = extractor.extract_tax_components(text, tax_type)
        for t in taxes:
            print(
                f"  {tax_type.upper():4s}: Rate={t.get('rate', '')}% Amount={t.get('amount', '')}"
            )
    print("\n--- Item Lines ---")
    items = extractor.extract_items(text)
    for i, item in enumerate(items):
        print(f"  Item {i + 1}: {item}")
    print("\nYou can now edit extractor.py patterns and re-run.")


def generate_ground_truth_template(directory: str):
    print(f"\nGenerating ground truth template from: {directory}")
    processor = get_processor()
    results = run_on_directory(directory, processor)
    if not results:
        print("  No results to template.")
        return
    gt = {}
    for r in results:
        fname = r.get("file", "unknown")
        gt[fname] = {field: r.get(field, "") for field in FIELD_NAMES}
    with open(GROUND_TRUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(gt, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Template saved to {GROUND_TRUTH_FILE}")
    print("  >>> Edit this file with correct values, then re-run with --ground-truth")


def main():
    parser = argparse.ArgumentParser(
        description="Invoice Data Extractor - Training & Tuning Tool"
    )
    parser.add_argument(
        "--dir", default=SAMPLES_DIR, help="Directory containing invoice files"
    )
    parser.add_argument(
        "--ground-truth", default=GROUND_TRUTH_FILE, help="Ground truth JSON file"
    )
    parser.add_argument(
        "--tune", action="store_true", help="Interactive pattern tuning mode"
    )
    parser.add_argument(
        "--export-results",
        action="store_true",
        help="Export extraction results to output/",
    )
    parser.add_argument(
        "--gen-gt",
        action="store_true",
        help="Generate ground truth template from extraction results",
    )
    args = parser.parse_args()

    if args.tune:
        processor = get_processor()
        interactive_tune(processor)
        return

    print("\n=== Invoice Data Extractor - Training & Tuning ===\n")
    processor = get_processor()
    gt = load_ground_truth(args.ground_truth) if not args.gen_gt else {}

    if args.gen_gt:
        generate_ground_truth_template(args.dir)
        return

    print(f"Processing invoices from: {args.dir}")
    results = run_on_directory(args.dir, processor)

    if not results:
        print("\nNo results. Place invoices in sample_invoices/ and re-run.")
        return

    eval_data = None
    if gt:
        print("\nEvaluating against ground truth ...")
        eval_data = evaluate(results, gt)
        print(
            f"  Overall accuracy: {eval_data['summary'].get('overall_accuracy', 0):.1%}"
        )

    if args.export_results or eval_data:
        export_results(results, eval_data)

    print("\n--- Field Extraction Summary ---\n")
    for field in FIELD_NAMES:
        found = sum(1 for r in results if r.get(field))
        total = len(results)
        pct = found / total * 100 if total else 0
        bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
        print(f"  {field:20s} [{bar}] {found}/{total} ({pct:.0f}%)")


if __name__ == "__main__":
    main()
