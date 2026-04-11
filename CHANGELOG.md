# Invoice Data Extractor Pro - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-04-11

### 🎓 Added
- **Continuous Learning System** - ML-based pattern learning from user annotations
- **Per-Field Confidence Scoring** - Confidence scores with explainability for each extracted field
- **Annotation Interface** - Interactive UI for correcting extraction results
- **Learning Dashboard** - Real-time accuracy metrics and recommendations
- **Evaluation Script** - Comprehensive metrics with per-field accuracy reports
- **Multiple OCR Preprocessing Modes** - Basic, advanced, and aggressive modes
- **Pattern Weight Management** - Automatic weight updates based on learning
- **Ground Truth Comparison** - Evaluate extraction against known correct values
- **Docker Enhancement** - Hindi language support and Poppler for PDF
- **Comprehensive Test Suite** - Unit and integration tests with pytest

### 🔧 Changed
- Improved regex patterns with confidence tracking
- Enhanced Streamlit UI with annotation capabilities
- Updated Dockerfile with additional language packs
- Better error handling and logging
- Improved data validation for GSTIN and PAN

### 🐛 Fixed
- Fixed pattern matching returning incorrect tuple types
- Improved date normalization edge cases
- Better amount parsing with currency symbols
- Enhanced OCR confidence calculation

### 📚 Documentation
- Added comprehensive DEPLOYMENT.md guide
- Updated README with learning system documentation
- Added evaluation and training workflow docs
- Created CHANGELOG for version tracking

## [1.0.0] - 2025-03-10

### Initial Release

#### Features
- OCR extraction using Tesseract with OpenCV preprocessing
- Field extraction for 8+ invoice fields (GSTIN, PAN, amounts, dates)
- India-specific validation (GSTIN checksum, PAN format)
- Streamlit web UI for single and batch processing
- JSON and CSV export
- Batch processing support
- Data cleaning and normalization
- Docker support
- Setup wizard

#### Architecture
- Three-layer architecture: OCR → Extraction → Cleaning
- Regex-based pattern matching
- OpenCV image preprocessing pipeline
- PDF-to-image conversion support

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|--------------|
| 2.0.0 | 2026-04-11 | Continuous learning, confidence scoring, annotation UI |
| 1.0.0 | 2025-03-10 | Initial release with basic OCR extraction |

---

## Upgrade Guide

### From v1.0 to v2.0

1. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run setup wizard:**
   ```bash
   python setup.py
   ```

3. **Start using new features:**
   - Open the web UI: `streamlit run app.py`
   - Navigate to the "Learning" tab to see the dashboard
   - Use the annotation interface to correct extractions
   - View accuracy metrics and recommendations

4. **Migrate existing data:**
   - Old results are compatible with v2.0
   - No data migration required
   - Models and annotations directories created automatically

---

*For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)*
