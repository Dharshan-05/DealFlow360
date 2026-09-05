# DealFlow360 — Backend Service

## Runtime Environment Strategy
- **Language**: Python 3.11+ (tested on Python 3.11.9)
- **Framework**: FastAPI with ASGI server Uvicorn
- **Isolation**: Local virtual environment in `backend/.venv/` (excluded from version control via root `.gitignore`)

## Setup Instructions

### 1. Create and Activate Virtual Environment
From the `backend/` directory:

```bash
# Windows
py -3.11 -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run Development Server
```bash
python run.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Base: `http://localhost:8000`
- API Health Check: `http://localhost:8000/api/v1/health`
- Legacy Health Check: `http://localhost:8000/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- ReDoc Docs: `http://localhost:8000/redoc`

### 4. Run Automated Tests
```bash
pytest
```
