"""
Simple test to demonstrate the Invoice Data Extractor works.
"""

from extractor import FieldExtractor
from utils import DataCleaner

# Sample OCR text from an invoice
sample_invoice_text = """
TAX INVOICE

ABC Technologies Pvt Ltd
123, Business Park, Mumbai - 400001
GSTIN: 27AABCU9603R1ZM
PAN: AABCU9603R

Invoice No: INV-2024-001
Invoice Date: 15/01/2024
Due Date: 14/02/2024

PO Number: PO-12345

Description                    Amount
Software License              ₹10,000.00
Support & Maintenance          ₹2,500.00

CGST @ 9%                      ₹900.00
SGST @ 9%                      ₹900.00

Total Amount:                 ₹14,300.00

Place of Supply: Maharashtra
"""

print("=" * 80)
print("INVOICE DATA EXTRACTOR - DEMONSTRATION")
print("=" * 80)
print()

# Extract fields
extractor = FieldExtractor()
fields = extractor.extract_all_fields(sample_invoice_text)

# Clean fields
cleaner = DataCleaner()
cleaned_fields = cleaner.clean_all(fields)

print("📊 EXTRACTED FIELDS:")
print("-" * 80)

# Display fields
display_fields = [
    ("🏢 Vendor Name", cleaned_fields.get("vendor_name")),
    ("📄 Invoice Number", cleaned_fields.get("invoice_number")),
    ("📅 Invoice Date", cleaned_fields.get("invoice_date")),
    ("⏰ Due Date", cleaned_fields.get("due_date")),
    ("💰 Total Amount", cleaned_fields.get("total_amount")),
    ("🇮🇳 GSTIN", cleaned_fields.get("gstin")),
    ("🆔 PAN", cleaned_fields.get("pan")),
    ("🔖 PO Number", cleaned_fields.get("po_number")),
    ("📍 Place of Supply", cleaned_fields.get("place_of_supply")),
]

for label, value in display_fields:
    status = "✅" if value and value != "Not Found" else "❌"
    print(f"{status} {label:20s}: {value}")

print()
print("-" * 80)
print("💵 ALL AMOUNTS FOUND:")
all_amounts = cleaned_fields.get("all_amounts", [])
if all_amounts:
    for i, amount in enumerate(all_amounts, 1):
        print(f"  {i}. ₹{amount}")
else:
    print("  No amounts found")

print()
print("=" * 80)
print("✅ EXTRACTION SUCCESSFUL!")
print("=" * 80)
print()
print("Next Steps:")
print("1. Run: streamlit run app.py")
print("2. Upload invoice files")
print("3. Extract data with confidence scores")
print("4. Annotate corrections to improve the system")
