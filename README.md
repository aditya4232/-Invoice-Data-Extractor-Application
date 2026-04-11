# Invoice Data Extractor Pro 🧾

**Automated Invoice Data Extraction using OCR + NLP**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.30+-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Problem Statement

Organizations process large numbers of invoices manually, which is time-consuming and error-prone. This project aims to automate the extraction of key information such as vendor name, invoice number, date, and total amount from invoice documents (PDF/images) using OCR and NLP techniques.

## 🎯 Objective

Build a system that:
1. ✅ Takes invoice (PDF/Image) as input
2. ✅ Extracts text using OCR (Tesseract)
3. ✅ Identifies key fields using NLP / rules
4. ✅ Outputs structured data (JSON/CSV)

## 💡 Solution

This application uses:
- **Tesseract OCR** to extract text from invoice images/PDFs
- **OpenCV** for image preprocessing
- **Regex-based NLP** to identify and extract 13+ invoice fields
- **Streamlit** for user-friendly web interface
- **Continuous Learning** to improve accuracy over time

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Tesseract OCR** (for automatic extraction)

Install Tesseract:
- **Windows**: https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### Installation

```bash
# Clone the repository
git clone https://github.com/aditya4232/Invoice-Data-Extractor-Application.git
cd Invoice-Data-Extractor-Application

# Install dependencies
pip install -r requirements.txt

# Test the extraction
python demo.py

# Run the application
streamlit run app.py
```

Open your browser to: **http://localhost:8501**

---

## 📊 Extracted Fields

| Field | Example | Description |
|-------|---------|-------------|
| vendor_name | ABC Technologies Pvt Ltd | Company/seller name |
| invoice_number | INV-2024-001 | Invoice identifier |
| invoice_date | 2024-01-15 | Invoice date (YYYY-MM-DD) |
| due_date | 2024-02-14 | Payment due date |
| total_amount | 14300.00 | Grand total |
| gstin | 27AABCU9603R1ZM | India GST Identification Number |
| pan | AABCU9603R | India Permanent Account Number |
| po_number | PO-12345 | Purchase Order number |
| place_of_supply | Maharashtra | State of supply |
| cgst_amount | 900.00 | Central GST amount |
| sgst_amount | 900.00 | State GST amount |
| igst_amount | Not Found | Integrated GST amount |
| all_amounts | [14300, 10000, 2500, 900] | All monetary values found |

---

## 🎨 Features

### Core Features
- ✅ **OCR Extraction** - Tesseract OCR with OpenCV preprocessing
- ✅ **Pattern-Based Extraction** - 13+ invoice fields with regex
- ✅ **India-Focused** - GSTIN, PAN, CGST/SGST/IGST extraction
- ✅ **Confidence Scoring** - Per-field accuracy metrics
- ✅ **Continuous Learning** - Improves with user annotations
- ✅ **Streamlit UI** - Upload invoices, extract data, annotate
- ✅ **Export** - JSON/CSV download
- ✅ **Batch Processing** - Process multiple invoices

### Advanced Features (v2.0)
- 🎓 **Continuous Learning System** - Learns from corrections
- 🎯 **Per-Field Confidence** - Know which fields to trust
- ✏️ **Annotation Interface** - Easy correction and training
- 📊 **Accuracy Dashboard** - Track extraction quality over time
- 🔬 **Evaluation Tools** - Comprehensive metrics and reports

---

## 📁 Project Structure

```
Invoice-Data-Extractor-Application/
│
├── app.py                    # Streamlit web UI
├── extractor.py              # Field extraction (regex + rules)
├── ocr.py                    # OCR engine (Tesseract + OpenCV)
├── utils.py                  # Processing pipeline & data cleaning
├── advanced_training.py      # Continuous learning system
├── demo.py                   # Simple demonstration script
├── evaluate.py               # Evaluation & metrics
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
├── Dockerfile                # Docker deployment
├── Procfile                  # Heroku deployment
├── README.md                 # This file
├── sample_invoices/          # Sample invoice files
├── output/                   # Extraction results
├── logs/                     # Application logs
├── models/                   # Trained pattern weights
└── annotations/              # User annotations
```

---

## 🛠️ How It Works

### 1. OCR Extraction
```python
from ocr import OCRExtractor

ocr = OCRExtractor()
text = ocr.extract_text('invoice.jpg')
```

### 2. Field Extraction
```python
from extractor import FieldExtractor

extractor = FieldExtractor()
fields = extractor.extract_all_fields(text)
```

### 3. Data Cleaning
```python
from utils import DataCleaner

cleaner = DataCleaner()
cleaned_fields = cleaner.clean_all(fields)
```

### 4. Full Pipeline
```python
from utils import InvoiceProcessor

processor = InvoiceProcessor()
result = processor.process_invoice('invoice.jpg')
print(result['fields'])
```

---

## 📦 Installation & Setup

### Windows

```bash
# 1. Install Python 3.8+
# 2. Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# 3. Clone repository
git clone https://github.com/aditya4232/Invoice-Data-Extractor-Application.git
cd Invoice-Data-Extractor-Application

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set Tesseract path in .env file
copy .env.example .env
# Edit .env and set: TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# 6. Run demo
python demo.py

# 7. Start app
streamlit run app.py
```

### macOS / Linux

```bash
# 1. Install Tesseract
brew install tesseract  # macOS
sudo apt-get install tesseract-ocr  # Linux

# 2. Clone and setup
git clone https://github.com/aditya4232/Invoice-Data-Extractor-Application.git
cd Invoice-Data-Extractor-Application
pip install -r requirements.txt

# 3. Run
python demo.py
streamlit run app.py
```

---

## 🐳 Docker Deployment

```bash
# Build
docker build -t invoice-extractor .

# Run
docker run -d -p 8501:8501 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/annotations:/app/annotations \
  invoice-extractor
```

Open: **http://localhost:8501**

---

## ☁️ Cloud Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Deploy your repository
4. App will be live at: `https://<your-app>.streamlit.app`

**Note:** Streamlit Cloud doesn't support Tesseract OCR. Use manual text input mode or deploy to Railway/Heroku for full functionality.

### Railway (Recommended)

1. Go to https://railway.app
2. Connect GitHub
3. Deploy your repository
4. Railway automatically installs Tesseract
5. Your app will be live with full OCR support

### Heroku

```bash
heroku login
heroku create invoice-extractor-pro
heroku buildpacks:add --index 1 heroku-community/apt
heroku buildpacks:add --index 2 heroku/python
echo "tesseract-ocr" > Aptfile
echo "poppler-utils" >> Aptfile
git push heroku main
```

---

## 📈 Evaluation

```bash
# Run evaluation with ground truth
python evaluate.py --ground-truth ground_truth.json --verbose

# Export evaluation report
python evaluate.py --export-report
```

---

## 🎓 Continuous Learning

The application includes a continuous learning system that improves over time:

1. **Process Invoices** - Extract data using OCR + patterns
2. **Annotate Corrections** - Use the annotation interface to correct errors
3. **Automatic Learning** - System learns and improves pattern weights
4. **Track Progress** - View accuracy dashboard and recommendations

---

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run demo
python demo.py
```

---

## 📝 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.8+ | Core implementation |
| OCR | Tesseract 5.x | Text extraction from images |
| Image Processing | OpenCV 4.8+ | Preprocessing & enhancement |
| Web Framework | Streamlit 1.30+ | User interface |
| ML/Training | Custom pattern learning | Continuous improvement |
| Data Validation | Regex + dateutil | Field validation |
| Containerization | Docker | Production deployment |

---

## 📋 Example Output

```json
{
  "vendor_name": "ABC Technologies Pvt Ltd",
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "due_date": "2024-02-14",
  "total_amount": "14300.0",
  "gstin": "27AABCU9603R1ZM",
  "pan": "AABCU9603R",
  "po_number": "PO-12345",
  "place_of_supply": "Maharashtra",
  "cgst_amount": "900.0",
  "sgst_amount": "900.0",
  "igst_amount": "Not Found",
  "all_amounts": ["14,300.00", "10,000.00", "2,500.00", "900.00"]
}
```

---

## 📚 Documentation

- `README.md` - This file (overview and quick start)
- `DEPLOYMENT.md` - Comprehensive deployment guide
- `DEPLOY_NOW.md` - Quick deployment to Streamlit Cloud
- `PROJECT_SUMMARY.md` - Complete project documentation
- `CHANGELOG.md` - Version history

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Aditya**  
GitHub: [@aditya4232](https://github.com/aditya4232)

---

## 🙏 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [OpenCV](https://opencv.org/) - Image processing
- [Streamlit](https://streamlit.io/) - Web framework
- [pytesseract](https://github.com/madmaze/pytesseract) - Python wrapper

---

*Last updated: April 2026*  
*Version: 2.0.0*
