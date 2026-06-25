# PAIOS — Personal AI Operating System

PAIOS is a self-hosted, privacy-first AI Operating System designed to work as your digital twin. It automates career scouting, analyzes skill gaps, drafts outreach, manages communication queues, and provides a mock interview simulation system.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.12+**
- **Node.js 18+ & npm**
- **Docker & Docker Compose** (for production mode or quick database setup)

---

## 🛠️ Local Development Setup

To run PAIOS locally in development mode:

### 1. Database & Cache Services
Spin up the required database infrastructure (MongoDB, Redis, ChromaDB) via Docker:
```bash
docker compose up -d
```

### 2. Backend API Setup
Navigate to the `backend/` directory, set up your virtual environment, and install dependencies using `uv`:
```bash
cd backend
# Create environment
uv venv
# Activate environment (Windows)
.venv\Scripts\activate
# Activate environment (Mac/Linux)
source .venv/bin/activate

# Install dependencies (including dev tools)
uv sync --all-extras
```

Make sure to create/configure the `.env` file inside `backend/` containing:
```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=AGENT
SECRET_KEY=generate-a-secure-random-secret-key-min-32-chars
ENCRYPTION_KEY=fernet-encryption-key-for-pii
OLLAMA_BASE_URL=http://localhost:11434
```

Start the FastAPI backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/system/health`

### 3. Frontend UI Setup
Navigate to the `frontend/` directory, install packages, and start the development server:
```bash
cd ../frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser. The Vite environment will automatically reverse-proxy API requests to port `8000`.

---

## 🐳 Production Deployment (Docker Compose)

To run the complete, containerized production environment (Databases + FastAPI Backend + React Frontend served via Nginx proxying):

```bash
docker compose -f docker-compose.prod.yml up --build -d
```
Once built, open `http://localhost` (port 80) to access the premium glassmorphic control center.

---

## 🧪 Verification & Tests

To run the test suite (48 passing unit tests including the API rate-limiter, database repositories, and agent execution layers):
```bash
cd backend
uv run --all-extras python -m pytest
```
