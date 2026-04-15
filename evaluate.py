"""
Invoice Data Extractor - Evaluation & Metrics Script

Run comprehensive evaluation on invoice extraction accuracy.
Generates detailed reports with per-field metrics and visualizations.

Usage:
    python evaluate.py                          # Run on all sample_invoices/
    python evaluate.py --dir path/to/invoices   # Custom invoice directory
    python evaluate.py --ground-truth gt.json   # Compare against ground truth
    python evaluate.py --export-report          # Export report to output/
    python evaluate.py --verbose                # Show detailed per-file results
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

from utils import InvoiceProcessor

GROUND_TRUTH_FILE = "ground_truth.json"
SAMPLES_DIR = "sample_invoices"
OUTPUT_DIR = "output"

FIELD_NAMES = [
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
]


def calculate_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity score (0.0 to 1.0)."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    s1, s2 = s1.lower().strip(), s2.lower().strip()

    if s1 == s2:
        return 1.0

    if s1 in s2 or s2 in s1:
        return 0.8

    # Levenshtein-based similarity
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 0.0

    # Simple character-level comparison
    common = sum(1 for a, b in zip(s1, s2) if a == b)
    return common / max_len


def evaluate_extraction(
    results: List[Dict], ground_truth: Dict[str, Dict]
) -> Dict[str, Any]:
    """Evaluate extraction results against ground truth."""
    evaluation = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(results),
        "files_with_ground_truth": 0,
        "per_file": {},
        "per_field": {},
        "overall": {},
    }

    field_scores = defaultdict(list)
    field_correct = defaultdict(int)
    field_total = defaultdict(int)

    files_evaluated = 0

    for result in results:
        file_name = result.get("file_name", "")
        gt = ground_truth.get(file_name, {})

        if not gt:
            continue

        files_evaluated += 1
        file_eval = {"fields": {}, "accuracy": 0.0}

        for field in FIELD_NAMES:
            expected = str(gt.get(field, "")).strip()
            if not expected:
                continue

            extracted = str(result.get("fields", {}).get(field, "")).strip()
            similarity = calculate_similarity(expected, extracted)

            field_scores[field].append(similarity)
            field_total[field] += 1

            if similarity > 0.9:
                field_correct[field] += 1

            file_eval["fields"][field] = {
                "expected": expected,
                "extracted": extracted,
                "similarity": round(similarity, 3),
                "correct": similarity > 0.9,
            }

        # Calculate file-level accuracy
        total_fields = len(file_eval["fields"])
        correct_fields = sum(1 for f in file_eval["fields"].values() if f["correct"])
        file_eval["accuracy"] = (
            correct_fields / total_fields if total_fields > 0 else 0.0
        )

        evaluation["per_file"][file_name] = file_eval

    evaluation["files_with_ground_truth"] = files_evaluated

    # Calculate per-field metrics
    for field in FIELD_NAMES:
        scores = field_scores[field]
        total = field_total[field]
        correct = field_correct[field]

        if scores:
            evaluation["per_field"][field] = {
                "accuracy": round(correct / total, 3) if total > 0 else 0.0,
                "avg_similarity": round(sum(scores) / len(scores), 3),
                "total_samples": total,
                "correct_predictions": correct,
                "min_similarity": round(min(scores), 3),
                "max_similarity": round(max(scores), 3),
            }

    # Calculate overall metrics
    all_accuracies = [f["accuracy"] for f in evaluation["per_field"].values()]
    evaluation["overall"] = {
        "average_accuracy": round(sum(all_accuracies) / len(all_accuracies), 3)
        if all_accuracies
        else 0.0,
        "fields_evaluated": len(evaluation["per_field"]),
        "total_comparisons": sum(field_total.values()),
        "total_correct": sum(field_correct.values()),
    }

    return evaluation


def print_evaluation_report(evaluation: Dict[str, Any], verbose: bool = False):
    """Print a comprehensive evaluation report."""
    print("\n" + "=" * 80)
    print("INVOICE DATA EXTRACTOR - EVALUATION REPORT")
    print("=" * 80)
    print(f"Timestamp: {evaluation['timestamp']}")
    print(f"Total Files: {evaluation['total_files']}")
    print(f"Files with Ground Truth: {evaluation['files_with_ground_truth']}")
    print("=" * 80)

    print("\n📊 OVERALL METRICS")
    print("-" * 80)
    overall = evaluation["overall"]
    print(f"  Average Accuracy:        {overall['average_accuracy']:.1%}")
    print(f"  Fields Evaluated:        {overall['fields_evaluated']}")
    print(f"  Total Comparisons:       {overall['total_comparisons']}")
    print(f"  Correct Predictions:     {overall['total_correct']}")
    print(
        f"  Overall Success Rate:    {overall['total_correct'] / overall['total_comparisons']:.1%}"
        if overall["total_comparisons"] > 0
        else "  Overall Success Rate:    N/A"
    )

    print("\n📈 PER-FIELD ACCURACY")
    print("-" * 80)
    for field, metrics in evaluation["per_field"].items():
        accuracy = metrics["accuracy"]
        avg_sim = metrics["avg_similarity"]
        total = metrics["total_samples"]
        correct = metrics["correct_predictions"]

        # Progress bar
        bar_length = 40
        filled = int(bar_length * accuracy)
        bar = "█" * filled + "░" * (bar_length - filled)

        status = "✅" if accuracy >= 0.9 else "⚠️" if accuracy >= 0.7 else "❌"

        print(f"\n  {field.upper():20s} {status} {accuracy:.1%} ({correct}/{total})")
        print(f"  {' ' * 22} [{bar}]")
        print(
            f"  {' ' * 22} Avg Similarity: {avg_sim:.3f} | Min: {metrics['min_similarity']:.3f} | Max: {metrics['max_similarity']:.3f}"
        )

    if verbose:
        print("\n\n📋 DETAILED PER-FILE RESULTS")
        print("-" * 80)
        for file_name, file_eval in evaluation["per_file"].items():
            print(f"\n📄 {file_name} (Accuracy: {file_eval['accuracy']:.1%})")
            for field, details in file_eval["fields"].items():
                status = "✅" if details["correct"] else "❌"
                print(
                    f"  {status} {field:20s}: Expected='{details['expected']}', Extracted='{details['extracted']}' (Similarity: {details['similarity']:.3f})"
                )

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    # Generate recommendations
    for field, metrics in evaluation["per_field"].items():
        if metrics["accuracy"] < 0.7:
            print(
                f"⚠️  {field.upper()}: Low accuracy ({metrics['accuracy']:.1%}). Consider:"
            )
            print(f"    - Adding more training samples")
            print(f"    - Improving regex patterns")
            print(f"    - Checking OCR quality")

    if evaluation["overall"]["average_accuracy"] >= 0.9:
        print(
            "✅ Overall performance is excellent! Keep adding annotations to maintain quality."
        )
    elif evaluation["overall"]["average_accuracy"] >= 0.7:
        print(
            "⚠️  Overall performance is good. Focus on low-accuracy fields to improve."
        )
    else:
        print("❌ Overall performance needs improvement. Consider:")
        print("    - Adding more annotated training data")
        print("    - Reviewing and improving regex patterns")
        print("    - Enhancing OCR preprocessing")

    print("=" * 80 + "\n")


def export_evaluation(evaluation: Dict[str, Any], output_dir: str = OUTPUT_DIR):
    """Export evaluation report to JSON file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_{timestamp}.json"
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Evaluation report exported to: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Invoice Data Extractor - Evaluation Script"
    )
    parser.add_argument(
        "--dir", default=SAMPLES_DIR, help="Directory containing invoice files"
    )
    parser.add_argument(
        "--ground-truth", default=GROUND_TRUTH_FILE, help="Ground truth JSON file"
    )
    parser.add_argument(
        "--export-report",
        action="store_true",
        help="Export evaluation report to output/",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed per-file results"
    )
    args = parser.parse_args()

    print("\n=== Invoice Data Extractor - Evaluation ===\n")

    # Load ground truth
    gt_path = Path(args.ground_truth)
    ground_truth = {}
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)
        print(f"✓ Loaded ground truth from {args.ground_truth}")
    else:
        print(f"⚠️  Ground truth file not found: {args.ground_truth}")
        print("   Running evaluation without ground truth comparison...")

    # Process invoices
    try:
        processor = InvoiceProcessor(enable_learning=False)
    except (ImportError, EnvironmentError) as e:
        print(f"  Cannot initialize processor: {e}")
        print("  Ensure Tesseract OCR is installed for full evaluation.")
        return
    print(f"\nProcessing invoices from: {args.dir}")

    from pathlib import Path

    dir_path = Path(args.dir)
    if not dir_path.exists():
        print(f"  ❌ Directory not found: {args.dir}")
        return

    exts = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
    files = sorted(
        f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in exts
    )

    if not files:
        print(f"  ⚠️  No invoice files found in {args.dir}")
        return

    print(f"  Found {len(files)} file(s)")

    results = []
    for i, file_path in enumerate(files, 1):
        print(
            f"  [{i}/{len(files)}] Processing {file_path.name}... ", end="", flush=True
        )
        try:
            result = processor.process_invoice(str(file_path))
            results.append(result)
            print("✅")
        except Exception as e:
            print(f"❌ Error: {e}")

    if not results:
        print("\n❌ No results to evaluate.")
        return

    # Evaluate
    if ground_truth:
        print("\n📊 Evaluating against ground truth...")
        evaluation = evaluate_extraction(results, ground_truth)
        print_evaluation_report(evaluation, verbose=args.verbose)

        if args.export_report:
            export_evaluation(evaluation)
    else:
        print("\n📊 Extraction Summary (without ground truth)")
        print("-" * 80)
        total = len(results)
        successful = sum(1 for r in results if r.get("success"))
        print(f"  Total Files: {total}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {total - successful}")
        print(
            f"  Success Rate: {successful / total:.1%}"
            if total > 0
            else "  Success Rate: N/A"
        )

        print("\n📈 Fields Found")
        print("-" * 80)
        for field in FIELD_NAMES:
            found = sum(
                1
                for r in results
                if r.get("success")
                and r.get("fields", {}).get(field) not in [None, "Not Found", ""]
            )
            pct = found / total if total > 0 else 0
            bar_length = 40
            filled = int(bar_length * pct)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"  {field:20s} [{bar}] {found}/{total} ({pct:.0%})")


if __name__ == "__main__":
    main()
