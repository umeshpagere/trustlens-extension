# TrustLens Backend (Flask)

TrustLens is a misinformation risk assessment API that analyzes text and images to determine their credibility and reliability. It combines Azure OpenAI–powered LLM analysis with lightweight, privacy-preserving heuristics to produce a final credibility score and verdict.

## Features

- Text analysis via Azure OpenAI with detailed, JSON-formatted explanations
- Image analysis using file heuristics (metadata size, reuse likelihood)
- Final weighted scoring (text 60% + image 40% when both are present)
- Hash-based deduplication and caching using MongoDB (optional)
- Strict JSON responses and centralized error handling

## System Requirements

- macOS, Linux, or Windows
- Python 3.11+ (virtual environment strongly recommended)
- Optional:
  - Azure OpenAI account and deployment for LLM analysis
  - MongoDB instance/cluster for persistence and deduplication

## Quick Start

```bash
# 1) Clone or move into the project directory
cd trustlens-2-main

# 2) Create and activate a virtual environment
python3 -m venv .venv
# macOS/Linux
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

# 3) Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4) Configure environment variables
cp .env .env.backup 2>/dev/null || true
# Open .env in your editor and set values (see below)

# 5) Run the server (default port 5000)
python run.py
# Or choose a different port
# PORT=5001 python run.py
```

## Configuration

Create or edit a `.env` file in the project root with the following variables:

```env
# Azure OpenAI (optional but recommended for full text/image LLM analysis)
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
AZURE_OPENAI_API_KEY=YOUR-AZURE-OPENAI-API-KEY
AZURE_OPENAI_DEPLOYMENT=YOUR-DEPLOYMENT-NAME
AZURE_OPENAI_API_VERSION=2024-10-21

# Server
PORT=5000

# MongoDB (optional; enables caching/reuse by content hash)
MONGODB_URI=mongodb+srv://USER:PASS@CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=trustlensDB
MONGODB_COLLECTION=analysis_records
```

Notes:
- If Azure variables are not set, the API still runs but will skip LLM-dependent features where required.
- If MongoDB is not configured or `pymongo` is unavailable, the API runs without persistence (no reuse by hash).

## Running

```bash
# Development (auto-reload is handled by Flask's dev server in run.py)
python run.py

# Choose a port
PORT=5001 python run.py

# Production (example using gunicorn)
gunicorn -b 0.0.0.0:${PORT:-5000} run:app
```

The server listens on `http://127.0.0.1:PORT` (default `5000`).

## API Reference

### Base URL

```
http://localhost:5000
```

### Health Check

GET `/api/health`

Response:

```json
{ "status": "TrustLens API running" }
```

### Analyze

POST `/api/analyze`

Request body (provide at least one of `text` or `imageUrl`):

```json
{
  "text": "Your text here (optional, min 5 chars if provided)",
  "imageUrl": "https://example.com/image.jpg" 
}
```

Response (shape varies based on inputs and available services):

```json
{
  "success": true,
  "textAnalysis": {
    "riskLevel": "low" | "medium" | "high",
    "riskKeywordsFound": ["keyword1", "keyword2"],
    "credibilityScore": 100,
    "verdict": "Reliable" | "Questionable" | "High Risk",
    "explanation": "LLM explanation if available"
  },
  "imageAnalysis": {
    "status": "processed" | "skipped",
    "metadata": { /* lightweight metadata */ },
    "tracing": { /* reuse likelihood */ },
    "credibilityScore": 85,
    "verdict": "Reliable" | "Questionable" | "High Risk"
  },
  "finalResult": {
    "finalScore": 95,
    "finalVerdict": "Reliable" | "Questionable" | "High Risk"
  }
}
```

Error response:

```json
{ "success": false, "message": "Error description" }
```

## Usage Examples

### cURL (text only)

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a sample news article to verify for misinformation"
  }'
```

### cURL (text + image)

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Breaking news: Check this image",
    "imageUrl": "https://example.com/news-image.jpg"
  }'
```

### Python

```python
import requests

url = "http://localhost:5000/api/analyze"
payload = {
    "text": "Your text content here",
    "imageUrl": "https://example.com/image.jpg"  # optional
}

resp = requests.post(url, json=payload, timeout=20)
print(resp.status_code, resp.json())
```

## Project Structure

```
trustlens-2-main/
├── app/
│   ├── config/                 # App & Azure settings
│   ├── models/                 # Pydantic schemas
│   ├── routes/                 # Flask blueprints (API)
│   ├── services/               # Analysis, scoring, storage
│   └── utils/                  # Hashing & image fetching
├── public/                     # Simple demo UI
├── extension/                  # Browser extension (optional)
├── run.py                      # Entry point (Flask)
├── requirements.txt            # Python deps
└── README.md                   # This file
```

## Troubleshooting

- Port in use
  - Symptom: “Address already in use”
  - Fix: Choose a different port  
    `PORT=5001 python run.py`

- PEP 668 / “externally managed environment”
  - Symptom: pip install error on macOS/Linux
  - Fix: Use a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    ```

- Azure OpenAI errors
  - Verify `.env` values for `AZURE_OPENAI_*` variables
  - The API runs without Azure OpenAI; LLM-only features will be limited

- MongoDB persistence disabled
  - Set `MONGODB_URI` in `.env` and ensure `pymongo` is installed (via requirements)
  - For Atlas, use your SRV connection string; ensure DNS/SSL are allowed

- Image analysis skipped
  - Ensure `imageUrl` is reachable; non-image URLs may be skipped

## Contribution Guidelines

1. Fork the repository and create a new branch:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Use a virtual environment and install dependencies.
3. Make changes following existing patterns and security practices.
4. Test endpoints locally (health and analyze).
5. Open a pull request with a clear description and testing notes.

## Security Notes

- Never commit `.env` or secrets to version control
- Keys must be stored in secure secret managers for deployment

## License

This repository does not declare a license. To open-source, add a `LICENSE` file (e.g., MIT, Apache-2.0). Otherwise, all rights are reserved by default.

## Support

For issues and questions, please open an issue or contact the maintainers.
