# SentinelVoice — Enterprise Deployment Guide

> Canonical Product: **SentinelVoice**  
> Target Environments: Local Docker Compose, Staging, Azure Enterprise Container Architecture.

---

## 1. Prerequisites

- **Python**: 3.11 or 3.12
- **Node.js**: v20 or v24 LTS + npm
- **Database**: PostgreSQL 15+ (Production) or SQLite (Local Development only)
- **Message Broker & Cache**: Redis 7+
- **Container Runtime**: Docker & Docker Compose v2+

---

## 2. Environment Configuration

Copy the appropriate template:
```bash
# For local development
cp backend/.env.development.example backend/.env

# For production staging
cp backend/.env.production.example backend/.env
```

### Critical Production Invariants:
In `APP_MODE=production`:
- `DATABASE_URL` must point to PostgreSQL (`postgresql://...`). SQLite fallback is strictly prohibited and causes immediate startup failure.
- `SECRET_KEY` must be at least 32 cryptographically random bytes (cannot contain default/dev words).
- `CORS_ORIGINS` must list explicit origins (cannot be wildcard `*`).
- `AI_PROVIDER` must be set to `azure` or `local` (demo provider cannot silently execute in production).

---

## 3. Database Migrations (Alembic)

SentinelVoice uses Alembic for declarative, version-controlled relational schema migrations:

```bash
cd backend

# Apply all migrations to the latest revision
python -m alembic upgrade head

# Inspect current revision status
python -m alembic current
```

---

## 4. Running with Docker Compose (Recommended)

To launch the entire platform stack (PostgreSQL, Redis, FastAPI Backend, and Next.js Frontend):

```bash
# Build and start all services in detached mode
docker-compose up --build -d

# Verify service health status
docker-compose ps
```

Services exposed:
- **Frontend SOC Console**: `http://localhost:3000`
- **Backend API & Swagger Docs**: `http://localhost:8000/docs`
- **Health Readiness Probe**: `http://localhost:8000/health/ready`
- **Health Liveness Probe**: `http://localhost:8000/health/live`
- **PostgreSQL Database**: `localhost:5432`
- **Redis Cache**: `localhost:6379`

---

## 5. Running Natively for Development

### Backend:
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 6. Microsoft Azure Production Deployment Architecture

```
Internet / Telephony Gateway
       │
Azure Front Door / WAF (DDoS protection, TLS termination)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
Azure Static Web Apps / Container App   Azure Container Apps
(Next.js Standalone Frontend)          (FastAPI Backend Microservice)
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
      Azure AI Speech (STT)      Azure OpenAI (GPT-4o)   Azure Cache for Redis
                 │                       │
                 └───────────────────────┴───────────────────────┐
                                                                 ▼
                                                    Azure Database for PostgreSQL
                                                    (Flexible Server, Private VNet)
```

### Security Hardening on Azure:
1. **Managed Identity**: Use Azure Managed Identities for Container Apps to access Azure PostgreSQL and Azure OpenAI without long-lived API keys.
2. **Key Vault Integration**: Mount secrets (JWT signing keys, database passwords) directly from Azure Key Vault into container environment variables.
3. **Private Networking**: Place Azure PostgreSQL and Redis inside a private virtual network (VNet) with Private Endpoints, disabling public internet ingress.
