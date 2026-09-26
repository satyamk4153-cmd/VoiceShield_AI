# SentinelVoice — Azure Production Deployment Guide

This guide details the enterprise production mapping of SentinelVoice into Microsoft Azure cloud services.

## Service Mapping Table

| Component | Local / Container Dev | Microsoft Azure Production Target |
|---|---|---|
| **Frontend SOC Dashboard** | Next.js on Container (Port 3000) | **Azure Static Web Apps** / **Azure App Service** |
| **Backend Core API & Risk Engine** | FastAPI on Container (Port 8000) | **Azure Container Apps** (Serverless KEDA autoscaling) |
| **Generative & Semantic Intent Engine** | Deterministic Demo Engine / Rule Graph | **Azure OpenAI Service** (`gpt-4o` deployment) |
| **Speech-to-Text & Acoustic Analysis** | Local Audio Processing (NumPy/SciPy/Wave) | **Azure AI Speech** (Fast Transcribe & Speaker Profile API) |
| **Entity & Fraud Signal NLP** | Semantic Lexical Graph | **Azure AI Language** (Conversational PII & Text Analytics) |
| **Metadata & Threat Storage** | PostgreSQL 15 / SQLite fallback | **Azure Database for PostgreSQL Flexible Server** |
| **Ephemeral Buffer & Models** | Local RAM / Temp storage | **Azure Blob Storage** (Private endpoint + Lifecycle policy) |
| **Enterprise Identity & Auth** | API Key / Session Token | **Microsoft Entra ID** (OAuth2 / OIDC SAML) |
| **SOC Intelligence & Reporting** | Recharts Embedded Analytics | **Microsoft Fabric / Power BI Embedded** |

---

## Environment Variable Configuration (Azure Key Vault)

```env
# Cloud AI Provider Mode
AI_PROVIDER=azure

# Database
DATABASE_URL=postgresql://sentineladmin@sentinel-pg-prod.postgres.database.azure.com:5432/sentinelvoice?sslmode=require

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://sentinel-ai-eastus.openai.azure.com/
AZURE_OPENAI_API_KEY=********
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure AI Speech
AZURE_SPEECH_ENDPOINT=https://eastus.api.cognitive.microsoft.com/
AZURE_SPEECH_KEY=********
AZURE_SPEECH_REGION=eastus

# Azure AI Language
AZURE_LANGUAGE_ENDPOINT=https://sentinel-lang-eastus.cognitiveservices.azure.com/
AZURE_LANGUAGE_KEY=********

# Security & CORS
MAX_AUDIO_SIZE_MB=25
CORS_ORIGINS=https://sentinelvoice.azurestaticapps.net,https://sentinel-soc.contoso.com
```
