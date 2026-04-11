# Deployment Guide - Invoice Data Extractor Pro

This guide covers multiple deployment options for the Invoice Data Extractor application.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Streamlit Cloud](#streamlit-cloud)
4. [Heroku Deployment](#heroku-deployment)
5. [AWS/GCP/Azure](#cloud-deployment)
6. [Production Best Practices](#production-best-practices)

---

## Local Development

### Prerequisites
- Python 3.8+
- Tesseract OCR
- Poppler (for PDF support)

### Setup
```bash
# 1. Clone or download the project
cd "Invoice Data Extractor Application"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and set TESSERACT_CMD path if needed

# 4. Run setup wizard (optional)
python setup.py

# 5. Start the application
streamlit run app.py
```

The app will be available at `http://localhost:8501`

---

## Docker Deployment

### Build and Run Locally

```bash
# Build the Docker image
docker build -t invoice-extractor-pro .

# Run the container
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/sample_invoices:/app/sample_invoices \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/annotations:/app/annotations \
  --name invoice-extractor \
  invoice-extractor-pro
```

### Docker Compose (Optional)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  invoice-extractor:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./sample_invoices:/app/sample_invoices
      - ./output:/app/output
      - ./models:/app/models
      - ./annotations:/app/annotations
    environment:
      - TESSERACT_CMD=/usr/bin/tesseract
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

---

## Streamlit Cloud

Streamlit Cloud offers free hosting for Streamlit apps.

### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Connect your GitHub repository
   - Set:
     - Repository: Your repo
     - Branch: main
     - Main file path: app.py
     - Python version: 3.11

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to Settings > Secrets
   - Add any required environment variables

**Note:** Streamlit Cloud has limitations:
- Cannot install system packages (Tesseract, Poppler)
- Limited to pure Python dependencies
- Best for demo/testing, not production OCR

---

## Heroku Deployment

### Prerequisites
- Heroku CLI installed
- Heroku account

### Steps:

```bash
# 1. Login to Heroku
heroku login

# 2. Create Heroku app
heroku create invoice-extractor-pro

# 3. Set buildpacks
heroku buildpacks:add --index 1 heroku-community/apt
heroku buildpacks:add --index 2 heroku/python

# 4. Create Aptfile for system dependencies
echo "tesseract-ocr" > Aptfile
echo "poppler-utils" >> Aptfile

# 5. Deploy
git push heroku main

# 6. Open the app
heroku open
```

### Heroku Environment Variables
```bash
heroku config:set PYTHONUNBUFFERED=1
heroku config:set DISABLE_COLLECTSTATIC=1
```

---

## Cloud Deployment

### AWS (EC2)

```bash
# 1. Launch Ubuntu EC2 instance

# 2. Install dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv tesseract-ocr poppler-utils

# 3. Clone and setup
git clone <your-repo>
cd invoice-extractor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Run with systemd
sudo nano /etc/systemd/system/invoice-extractor.service
```

Service file:
```ini
[Unit]
Description=Invoice Data Extractor
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/invoice-extractor
ExecStart=/home/ubuntu/invoice-extractor/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable invoice-extractor
sudo systemctl start invoice-extractor
```

### GCP (Cloud Run)

```bash
# 1. Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/invoice-extractor

# 2. Deploy to Cloud Run
gcloud run deploy invoice-extractor \
  --image gcr.io/PROJECT-ID/invoice-extractor \
  --platform managed \
  --port 8501 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300
```

### Azure (Container Instances)

```bash
# 1. Build and push to Azure Container Registry
az acr build --registry <registry-name> --image invoice-extractor:latest .

# 2. Deploy to Container Instances
az container create \
  --resource-group <resource-group> \
  --name invoice-extractor \
  --image <registry-name>.azurecr.io/invoice-extractor:latest \
  --dns-name-label invoice-extractor \
  --ports 8501 \
  --cpu 2 \
  --memory 4
```

---

## Production Best Practices

### 1. Security
- Use environment variables for sensitive data
- Enable HTTPS (use reverse proxy like Nginx)
- Implement rate limiting
- Regular dependency updates

### 2. Performance
- Use Gunicorn with Streamlit:
  ```bash
  pip install streamlit opencv-python-headless
  # Run with multiple workers
  streamlit run app.py --server.port=8501
  ```
- Enable caching for OCR results
- Use Redis for session management

### 3. Monitoring
- Set up logging to external service (CloudWatch, Datadog)
- Monitor OCR accuracy over time
- Track annotation quality metrics

### 4. Scaling
- Use horizontal pod autoscaling (Kubernetes)
- Implement load balancing
- Use CDN for static assets

### 5. Backup
- Regular backup of:
  - `models/` directory (trained patterns)
  - `annotations/` directory (training data)
  - `output/` directory (results)

---

## Environment Variables

### Required
- `TESSERACT_CMD` - Path to Tesseract executable (Windows only)

### Optional
- `OUTPUT_DIR` - Output directory (default: output)
- `LOGS_DIR` - Logs directory (default: logs)
- `PREPROCESS_DEFAULT` - Enable preprocessing (default: True)
- `CONFIDENCE_THRESHOLD` - Minimum confidence (default: 50)

---

## Troubleshooting

### Tesseract Not Found
```bash
# Windows: Set in .env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Linux
sudo apt install tesseract-ocr

# macOS
brew install tesseract
```

### PDF Conversion Fails
```bash
# Install poppler
# Ubuntu
sudo apt install poppler-utils

# macOS
brew install poppler

# Windows
# Download from: https://github.com/oschwartz10612/poppler-windows/releases
# Add to PATH
```

### Port Already in Use
```bash
streamlit run app.py --server.port 8502
```

### Out of Memory
- Increase container memory limit
- Reduce batch size
- Optimize image preprocessing

---

## Support

For issues and questions:
- GitHub Issues: <your-repo>/issues
- Email: <your-email>

---

*Last updated: April 2026*
