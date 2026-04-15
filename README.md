# Invoice Data Extractor

AI-powered extraction of key fields from Indian invoice documents using OCR and pattern matching.

## Features

- **OCR Extraction** - Tesseract with OpenCV preprocessing
- **13+ Fields** - GSTIN, PAN, invoice number, dates, amounts, tax components
- **Confidence Scoring** - Per-field accuracy metrics
- **Continuous Learning** - Improves from user corrections
- **Export** - JSON/CSV download

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Railway (Free)

1. Push to GitHub
2. Go to https://railway.app → Login with GitHub
3. New Project → Deploy from GitHub → Select repo
4. Done! Full OCR works automatically.

See [DEPLOYMENT.md](DEPLOYMENT.md) for more options.

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

Python 3.11 | Streamlit | Tesseract OCR | OpenCV | Pandas