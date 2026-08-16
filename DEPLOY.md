# Deploying MCP Project to Railway

## Architecture
This project has **2 services** that run separately:
- **Service 1: MCP Server** — exposes tools (weather, email, calendar, datetime) via HTTP at `/mcp`
- **Service 2: Client UI** — a web chat interface that connects to the MCP Server

---

## Step-by-step Railway Deployment

### Prerequisites
- GitHub account
- Railway account (free at https://railway.app)
- API keys: GROQ_API_KEY, WEATHER_API_KEY, NYLAS_API_KEY, NYLAS_GRANT_ID

---

### 1. Push your code to GitHub
Create a new GitHub repo and push this project folder to it.

---

### 2. Deploy Service 1 — MCP Server

1. Go to https://railway.app → New Project → Deploy from GitHub repo
2. Select your repo
3. Railway auto-detects Python via `requirements.txt`
4. Set the **Start Command** to: `python -m server.app`
5. Add Environment Variables:
   - `WEATHER_API_KEY` = your OpenWeather key
   - `NYLAS_API_KEY` = your Nylas key
   - `NYLAS_GRANT_ID` = your Nylas grant ID
6. Generate a domain: Settings → Networking → Generate Domain
7. Copy the public URL, e.g. `https://mcp-server-xyz.railway.app`

---

### 3. Deploy Service 2 — Client UI

1. In the same Railway project → Add Service → GitHub Repo (same repo)
2. Set the **Start Command** to: `python -m client.ui`
3. Add Environment Variables:
   - `GROQ_API_KEY` = your Groq API key
   - `MCP_SERVER_URL` = `https://mcp-server-xyz.railway.app/mcp`  ← paste your server URL from step 2
   - `MODEL_NAME` = `llama-3.1-8b-instant`
4. Generate a domain for this service too
5. Open the domain — your chat UI is live! 🎉

---

## Local Development

```bash
# Copy and fill in your keys
cp .env.example .env

# Terminal 1 — run MCP Server
python -m server.app

# Terminal 2 — run Client UI
python -m client.ui
# Open http://localhost:8080
```

## Environment Variables Reference

| Variable | Service | Description |
|---|---|---|
| `WEATHER_API_KEY` | Server | OpenWeatherMap API key |
| `NYLAS_API_KEY` | Server | Nylas API key for email/calendar |
| `NYLAS_GRANT_ID` | Server | Nylas grant ID |
| `GROQ_API_KEY` | Client | Groq API key for LLM |
| `MODEL_NAME` | Client | Groq model (default: llama-3.1-8b-instant) |
| `MCP_SERVER_URL` | Client | Full URL to MCP server `/mcp` endpoint |
