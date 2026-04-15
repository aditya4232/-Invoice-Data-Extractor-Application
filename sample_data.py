SAMPLE_INVOICES = {
    "indian_gst_invoice_001": """
TAX INVOICE

ABC Technologies Pvt Ltd
123, Bandra Kurla Complex, Mumbai - 400051
Maharashtra, India
GSTIN: 27AABCU9603R1ZM
PAN: AABCU9603R
State: Maharashtra, Code: 27

Invoice No: INV-2024-001
Invoice Date: 15/01/2024
Due Date: 14/02/2024
PO Number: PO-12345

Billed To:
XYZ Corporation Ltd
456, Nehru Place, New Delhi - 110019
GSTIN: 07AABCP1234Q1Z5

SL   Description                    HSN/SAC   Qty   Rate      Amount
1    Software License              998314    1     10,000.00  10,000.00
2    Annual Support & Maintenance   998314    1      2,500.00   2,500.00

                              Subtotal:         12,500.00
CGST @ 9%                                  1,125.00
SGST @ 9%                                  1,125.00

Grand Total:             14,750.00
Amount in Words: Fourteen Thousand Seven Hundred Fifty Rupees Only

Place of Supply: Maharashtra

For ABC Technologies Pvt Ltd
Authorised Signatory
""",
    "indian_gst_invoice_002": """
TAX INVOICE

Reliance Retail Limited
Maker Chambers IV, 222, Nariman Point
Mumbai, Maharashtra - 400021
GSTIN: 27AABCR5678P1Z3
PAN: AABCR5678P

Invoice No: RLN/2024/MAR/00567
Date: 05-03-2024
Due Date: 04-04-2024

Sold To:
Tata Consultancy Services Ltd
TCS House, Raveline Street, Fort
Mumbai - 400001

SL   Description         HSN Code   Qty   Rate      Amount
1    IT Consulting       998313     10    25,000.00  2,50,000.00
2    Cloud Services      998315     5     50,000.00  2,50,000.00

                    Sub Total:    5,00,000.00
CGST @ 9%:                        45,000.00
SGST @ 9%:                        45,000.00

Total Amount:          5,90,000.00
Amount in Words: Five Lakh Ninety Thousand Rupees Only

Place of Supply: Maharashtra
PO Number: PO-2024-TCS-789

For Reliance Retail Limited
""",
    "indian_gst_invoice_003": """
COMMERCIAL INVOICE

Wipro Technologies Pvt Ltd
Doddakannelli, Sarjapur Road
Bengaluru, Karnataka - 560035
GSTIN: 29AABCW1234P1Z3
PAN: AABCW1234P

Ref: CI-2024-555
Date of Invoice: 25th March 2024

Bill To:
Infosys Limited
44, Electronics City
Bengaluru, Karnataka - 560100

Description                  Amount (INR)
Application Development       18,50,000.00
Testing Services              3,75,000.00

IGST @ 18%:                  4,03,500.00

Amount Payable:              26,28,500.00
(Rupees Twenty Six Lakh Twenty Eight Thousand Five Hundred Only)

PO No: WIPRO-PO-2024-001
Place of Supply: Karnataka
""",
    "international_invoice_001": """
INVOICE

Global Tech Solutions Inc.
100 Innovation Drive, Suite 400
San Francisco, CA 94105
United States

Invoice #: INV-INT-2024-421
Date: 2024/02/28
Due Date: 2024/03/30

Bill To:
Acme Corporation
200 Business Park Avenue
London, UK SW1A 1AA

Description                  Quantity   Unit Price   Total
Cloud Infrastructure          12         $2,500     $30,000
Managed Services               3         $5,000     $15,000
24/7 Support Package           1         $8,000      $8,000

                                    Subtotal: $53,000
Tax (VAT 20%):                          $10,600

TOTAL AMOUNT DUE:                       $63,600

Payment Terms: Net 30
PO Number: ACME-PO-2024-111
""",
    "minimal_invoice_001": """
INVOICE

Small Business Solutions
GSTIN: 06AABCF1234Q1Z8

Invoice No: SBS-24-078
Date: 10/04/2024

Web Development Services: 25,000
CGST @ 9%: 2,250
SGST @ 9%: 2,250

Total: 29,500

Thank you for your business!
""",
    "edge_case_no_gstin": """
INVOICE

Freelance Developer
Independent Contractor

Invoice Number: FREELANCE/2024/001
Date: 22/05/2024
Due: 21/06/2024

Services Rendered:
- Website Redesign: 45,000
- SEO Optimization: 15,000

Subtotal: 60,000
Grand Total: 60,000

Payment via bank transfer only.
PO Number: PO-FREELANCE-42
""",
    "edge_case_multiple_amounts": """
TAX INVOICE

Mega Corp India Ltd
GSTIN: 07AABCM9999Q1Z1

Invoice No: MEGA-INV-2024-999
Date: 30/06/2024

Items:
1. Server Hardware   2,50,000.00
2. Software License   1,25,000.00
3. Annual Maintenance   50,000.00
4. Installation        25,000.00
5. Training            15,000.00

Subtotal: 4,65,000.00
CGST @ 9%: 41,850.00
SGST @ 9%: 41,850.00
Discount (5%): -23,250.00

Net Total: 5,25,450.00

Round Off: 5,25,450.00

Grand Total: 5,25,450.00
PAN: AABCM9999Q
""",
    "edge_case_igst_inter_state": """
TAX INVOICE

South India Exports Ltd
12, Mount Road, Chennai
Tamil Nadu - 600002
GSTIN: 33AABCS5678Q1Z5

Invoice/2024/CH/0045
Invoice Date: 18-07-2024

Ship To:
North India Traders
Delhi NCR, New Delhi - 110001

Products:
1. Textile Batch A    3,00,000.00
2. Textile Batch B    2,00,000.00

Sub Total: 5,00,000.00
IGST @ 18%: 90,000.00

Total Amount: 5,90,000.00

Place of Supply: Delhi
""",
}
