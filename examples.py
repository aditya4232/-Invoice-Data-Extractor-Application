"""
8 Working Examples for Invoice Data Extractor.

Demonstrates single processing, batch processing, custom extraction,
preprocessing, data cleaning, PDF handling, error handling, and export.
"""

import os
import sys
import json
from pathlib import Path


EXAMPLES = {}


def example_menu():
    print("\n" + "=" * 60)
    print("   Invoice Data Extractor - Examples")
    print("=" * 60)
    print()
    print("  0 - Run all examples")
    print("  1 - Single invoice processing")
    print("  2 - Batch processing")
    print("  3 - Custom field extraction")
    print("  4 - Image preprocessing comparison")
    print("  5 - Data cleaning & validation")
    print("  6 - PDF processing")
    print("  7 - Error handling & logging")
    print("  8 - Batch export (JSON + CSV)")
    print()
    print("  q - Quit")
    print()


def example_1():
    """Single invoice processing."""
    print("\n" + "-" * 60)
    print("Example 1: Single Invoice Processing")
    print("-" * 60)

    from utils import InvoiceProcessor

    processor = InvoiceProcessor()

    invoice_dir = Path("sample_invoices")
    if not invoice_dir.exists() or not list(invoice_dir.iterdir()):
        print("No sample invoices found in sample_invoices/ directory.")
        print("Place invoice files there and try again.")
        demo_text = """
        Invoice No: INV-2025-001
        Date: 10/03/2025
        From: ABC Technologies Pvt Ltd
        GSTIN: 27AAFUT5055K1Z0
        PAN: AAFUT5055K
        Total: Rs. 12,500.00
        Due Date: 25/03/2025
        PO Number: PO-98765
        """

        from extractor import FieldExtractor

        extractor = FieldExtractor()
        result = extractor.extract_all_fields(demo_text)
        print("\nDemo extraction from sample text:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    files = [f for f in invoice_dir.iterdir() if f.is_file()]
    if files:
        file_path = str(files[0])
        print(f"Processing: {file_path}")
        result = processor.process_invoice(file_path)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def example_2():
    """Batch processing of multiple invoices."""
    print("\n" + "-" * 60)
    print("Example 2: Batch Processing")
    print("-" * 60)

    from utils import InvoiceProcessor

    processor = InvoiceProcessor()

    invoice_dir = Path("sample_invoices")
    if not invoice_dir.exists():
        print("Creating sample_invoices/ directory...")
        invoice_dir.mkdir(parents=True, exist_ok=True)
        print("Place invoice files there and try again.")
        return

    print(f"Processing all files in {invoice_dir}/...")
    results = processor.process_batch(str(invoice_dir))
    print(f"Processed {len(results)} files")

    summary = processor.get_summary(results)
    print(f"\nSummary:")
    print(f"  Total: {summary['total']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success Rate: {summary['success_rate']}%")

    for result in results:
        status = "OK" if result.get("success") else "FAIL"
        print(f"  [{status}] {result.get('file_name', 'Unknown')}")


def example_3():
    """Custom field extraction with the FieldExtractor."""
    print("\n" + "-" * 60)
    print("Example 3: Custom Field Extraction")
    print("-" * 60)

    from extractor import FieldExtractor

    extractor = FieldExtractor()

    sample_texts = [
        """
        TAX INVOICE
        Invoice No: INV-2025-042
        Date: 15-March-2025
        Seller: Tata Consultancy Services Ltd
        GSTIN: 27AABCT1332B1Z5
        PAN: AABCT1332B
        Grand Total: INR 45,000.00
        PO No: PO-2025-123
        """,
        """
        BILL OF SUPPLY
        Invoice # BILL/2025/789
        Bill Date: 2025/03/20
        From: Infosys Limited
        GSTIN: 29AABCI1234P1Z8
        Total Amount Due: Rs.1,25,000
        Due: 05/04/2025
        """,
        """
        COMMERCIAL INVOICE
        Ref: CI-2025-555
        Date of Invoice: 25th March 2025
        Vendor: Wipro Technologies Pvt Ltd
        GST: 06AABCW1234P1Z3
        Amount Payable: INR 78,500.50
        """,
    ]

    for i, text in enumerate(sample_texts, 1):
        print(f"\n--- Sample {i} ---")
        result = extractor.extract_all_fields(text)
        for key, value in result.items():
            print(f"  {key}: {value}")


def example_4():
    """Compare OCR with and without preprocessing."""
    print("\n" + "-" * 60)
    print("Example 4: Image Preprocessing Comparison")
    print("-" * 60)

    try:
        from ocr import OCRExtractor

        ocr = OCRExtractor()
    except (ImportError, EnvironmentError) as e:
        print("Cannot initialize OCR engine.")
        print(f"Error: {e}")
        print("\nDemonstration of preprocessing steps:")
        print("  1. Convert to grayscale")
        print("  2. Apply bilateral filter (denoise)")
        print("  3. Apply Otsu's thresholding")
        print("  4. Apply morphological closing")
        print("  5. Upscale small images (< 100px)")
        print(
            "\nPreprocessing is enabled by default and improves accuracy significantly."
        )
        return

    invoice_dir = Path("sample_invoices")
    files = (
        [f for f in invoice_dir.iterdir() if f.is_file()]
        if invoice_dir.exists()
        else []
    )

    if not files:
        print(
            "No sample files found. Place invoices in sample_invoices/ and try again."
        )
        print("\nPreprocessing pipeline description:")
        print(
            "  With preprocessing: grayscale -> denoise -> threshold -> close -> scale"
        )
        print("  Without: raw image directly to Tesseract")
        return

    for file_path in files[:1]:
        print(f"\nProcessing: {file_path.name}")
        try:
            text_raw = ocr.extract_text(str(file_path), preprocess=False)
            text_processed = ocr.extract_text(str(file_path), preprocess=True)
            conf_raw = ocr.get_confidence(str(file_path))

            print(f"\nWithout preprocessing ({len(text_raw)} chars, confidence: N/A):")
            print(f"  First 200 chars: {text_raw[:200]}...")

            print(f"\nWith preprocessing ({len(text_processed)} chars):")
            print(f"  First 200 chars: {text_processed[:200]}...")

            print(f"\nConfidence (preprocessed): {conf_raw:.1f}%")
        except Exception as e:
            print(f"Error: {e}")


def example_5():
    """Data cleaning and validation."""
    print("\n" + "-" * 60)
    print("Example 5: Data Cleaning & Validation")
    print("-" * 60)

    from utils import DataCleaner

    cleaner = DataCleaner()

    test_fields = {
        "vendor_name": "  ABC Technologies Pvt Ltd.  \n",
        "invoice_number": " INV-2025-001 ",
        "invoice_date": "10/03/2025",
        "due_date": "25th March 2025",
        "total_amount": "₹12,500.00",
        "gstin": " 27AAFUT5055K1Z0 ",
        "pan": " aafut5055k ",
        "po_number": " PO-2025-789 ",
    }

    print("Original fields:")
    for key, value in test_fields.items():
        print(f"  {key}: '{value}'")

    cleaned = cleaner.clean_all(test_fields)

    print("\nCleaned fields:")
    for key, value in cleaned.items():
        print(f"  {key}: '{value}'")

    print("\nValidation:")
    gstins_to_test = ["27AAFUT5055K1Z0", "INVALIDGSTIN123", "29AABCI1234P1Z8"]
    for gstin in gstins_to_test:
        valid = cleaner.validate_gstin(gstin)
        print(f"  GSTIN {gstin}: {'Valid' if valid else 'Invalid'}")

    pans_to_test = ["AAAAA1234A", "invalidpan1", "AABCT1332B"]
    for pan in pans_to_test:
        valid = cleaner.validate_pan(pan)
        print(f"  PAN {pan}: {'Valid' if valid else 'Invalid'}")


def example_6():
    """PDF processing."""
    print("\n" + "-" * 60)
    print("Example 6: PDF Processing")
    print("-" * 60)

    try:
        from pdf2image import convert_from_path

        print("pdf2image is available.")
    except ImportError:
        print("pdf2image is NOT installed.")
        print("Install with: pip install pdf2image")
        print("Also install poppler:")
        if sys.platform == "win32":
            print(
                "  Windows: https://github.com/oschwartz10612/poppler-windows/releases"
            )
        elif sys.platform == "darwin":
            print("  macOS: brew install poppler")
        else:
            print("  Linux: sudo apt-get install poppler-utils")
        return

    try:
        from ocr import OCRExtractor

        ocr = OCRExtractor()
    except EnvironmentError as e:
        print(f"OCR initialization error: {e}")
        return

    invoice_dir = Path("sample_invoices")
    pdfs = list(invoice_dir.glob("*.pdf")) if invoice_dir.exists() else []

    if not pdfs:
        print("No PDF files found in sample_invoices/.")
        print("Place a PDF invoice there and try again.")
        return

    for pdf_path in pdfs[:1]:
        print(f"\nProcessing: {pdf_path.name}")
        try:
            images = ocr.pdf_to_images(str(pdf_path))
            print(f"PDF has {len(images)} page(s)")

            text = ocr.extract_text(str(pdf_path))
            print(f"Extracted {len(text)} characters")

            from extractor import FieldExtractor

            extractor = FieldExtractor()
            result = extractor.extract_all_fields(text)
            print("\nExtracted fields:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error processing PDF: {e}")


def example_7():
    """Error handling and logging."""
    print("\n" + "-" * 60)
    print("Example 7: Error Handling & Logging")
    print("-" * 60)

    from utils import InvoiceProcessor

    print("Testing error handling scenarios:\n")

    print("1. File not found:")
    try:
        processor = InvoiceProcessor()
        processor.process_invoice("nonexistent_file.pdf")
    except FileNotFoundError as e:
        print(f"   Caught: FileNotFoundError - {e}")

    print("\n2. Unsupported file format:")
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test data")
            temp_path = f.name
        try:
            processor.process_invoice(temp_path)
        except ValueError as e:
            print(f"   Caught: ValueError - {e}")
        finally:
            os.unlink(temp_path)
    except Exception as e:
        print(f"   Error: {e}")

    print("\n3. Empty text extraction:")
    from extractor import FieldExtractor

    extractor = FieldExtractor()
    result = extractor.extract_all_fields("")
    print(f"   Result for empty text: {result}")

    print("\n4. Invalid data cleaning:")
    from utils import DataCleaner

    cleaner = DataCleaner()
    print(f"   Clean GSTIN 'invalid': {cleaner.clean_field('gstin', 'invalid')}")
    print(
        f"   Validate GSTIN '27AAFUT5055K1Z0': {cleaner.validate_gstin('27AAFUT5055K1Z0')}"
    )
    print(f"   Validate PAN 'AAAAA1234A': {cleaner.validate_pan('AAAAA1234A')}")

    print("\n5. Logging is active - check logs/ directory for log files")


def example_8():
    """Batch export to JSON and CSV."""
    print("\n" + "-" * 60)
    print("Example 8: Batch Export (JSON + CSV)")
    print("-" * 60)

    from utils import InvoiceProcessor

    processor = InvoiceProcessor()

    demo_results = [
        {
            "file_name": "invoice_001.jpg",
            "file_path": "/path/to/invoice_001.jpg",
            "success": True,
            "confidence": 92.5,
            "extraction_time": "0:00:03.123456",
            "fields": {
                "vendor_name": "ABC Technologies Pvt Ltd",
                "invoice_number": "INV-2025-001",
                "invoice_date": "2025-03-10",
                "due_date": "2025-03-25",
                "total_amount": "12500.0",
                "gstin": "27AAFUT5055K1Z0",
                "pan": "AAFUT5055K",
                "po_number": "PO-98765",
                "all_amounts": ["12,500.00", "500.00", "1,000.00"],
            },
            "error": None,
        },
        {
            "file_name": "invoice_002.png",
            "file_path": "/path/to/invoice_002.png",
            "success": True,
            "confidence": 87.3,
            "extraction_time": "0:00:04.567890",
            "fields": {
                "vendor_name": "TCS India",
                "invoice_number": "INV-2025-042",
                "invoice_date": "2025-03-15",
                "due_date": "2025-04-05",
                "total_amount": "45000.0",
                "gstin": "27AABCT1332B1Z5",
                "pan": "AABCT1332B",
                "po_number": "Not Found",
                "all_amounts": ["45,000.00", "5,000.00"],
            },
            "error": None,
        },
    ]

    print("Exporting demo results to JSON and CSV...\n")

    json_path = processor.save_results_json(demo_results, "output/demo_results.json")
    print(f"JSON saved to: {json_path}")

    csv_path = processor.save_results_csv(demo_results, "output/demo_results.csv")
    print(f"CSV saved to: {csv_path}")

    print("\nJSON content:")
    with open(json_path, "r", encoding="utf-8") as f:
        print(f.read()[:500] + "...\n")

    print("CSV content:")
    with open(csv_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < 3:
                print(f"  {line.rstrip()}")

    summary = processor.get_summary(demo_results)
    print(
        f"\nSummary: {summary['successful']}/{summary['total']} successful "
        f"({summary['success_rate']}%)"
    )


EXAMPLES = {
    "1": example_1,
    "2": example_2,
    "3": example_3,
    "4": example_4,
    "5": example_5,
    "6": example_6,
    "7": example_7,
    "8": example_8,
}


def main():
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice == "0":
            for func in EXAMPLES.values():
                try:
                    func()
                except Exception as e:
                    print(f"Error in example: {e}")
        elif choice in EXAMPLES:
            try:
                EXAMPLES[choice]()
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Invalid example number: {choice}")
        return

    while True:
        example_menu()
        choice = input("Select example (1-8, 0 for all, q to quit): ").strip().lower()

        if choice == "q":
            print("Goodbye!")
            break
        elif choice == "0":
            for func in EXAMPLES.values():
                try:
                    func()
                except Exception as e:
                    print(f"Error in example: {e}")
        elif choice in EXAMPLES:
            try:
                EXAMPLES[choice]()
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Invalid choice: {choice}")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
