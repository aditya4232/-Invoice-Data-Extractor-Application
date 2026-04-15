# Deployment Guide

## Railway (Recommended - Free, No Credit Card)

Railway gives **$5 free credits** on signup (GitHub login only, no credit card needed).

### Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Railway"
   git push origin main
   ```

2. **Deploy on Railway**
   - Go to https://railway.app
   - Click "Login with GitHub" (no credit card)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Dockerfile - click "Deploy"

3. **Wait 2-3 minutes** for build + deploy

4. **Your app is live** at `https://invoice-data-extractor.up.railway.app`

### Free Tier Details
- $5 credits/month (no credit card)
- 512MB RAM, 1GB disk
- Sleeps after 30min inactivity (auto-wakes)
- Full Tesseract OCR support

---

## Render (Alternative - Free but requires Credit Card)

Render has a free tier but **requires credit card**.

1. Push to GitHub

2. Go to https://render.com → Login → "New" → "Web Service"

3. Connect GitHub repo

4. Settings:
   - **Build Command**: Leave empty (uses Dockerfile)
   - **Start Command**: `streamlit run app.py --server.port $PORT`
   - **Plan**: Free

5. Click "Create Web Service"

---

## Docker (Local)

```bash
docker build -t invoice-extractor .
docker run -d -p 8501:8501 invoice-extractor
```

---

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Configuration

### Windows (Tesseract path)
```bash
copy .env.example .env
# Edit .env: TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Linux/macOS
```bash
# Usually auto-detected. If not:
export TESSERACT_CMD=/usr/bin/tesseract
```

---

## Troubleshooting

### Tesseract Not Found
```bash
# Windows
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Linux
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### PDF Support
```bash
# Linux
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### App Sleeping on Railway
Railway's free tier sleeps after 30min. It auto-wakes when accessed. This is normal for free tier.

---

## Quick Start Commands

```bash
# Clone and run locally
git clone <your-repo>
cd invoice-data-extractor
pip install -r requirements.txt
streamlit run app.py

# Run tests
pytest tests/ -v
```