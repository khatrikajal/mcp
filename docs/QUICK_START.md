# AI Workforce Platform - Quick Start Guide

## 5-Minute Setup

### 1. Clone and Configure

```bash
git clone <repository-url>
cd mcp
cp .env.example .env
```

Edit `.env` with your API keys:
```env
GROQ_API_KEY=your_groq_api_key
NYLAS_API_KEY=your_nylas_api_key
NYLAS_GRANT_ID=your_nylas_grant_id
JWT_SECRET=your_secret_key_change_in_production
```

### 2. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m backend.main
```

Backend runs on: `http://localhost:8001`

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:5173`

### 4. First Login

1. Open `http://localhost:5173`
2. Click "Register"
3. Create account with:
   - Email: your@email.com
   - Name: Your Name
   - Password: (min 8 chars, uppercase, lowercase, digit)

---

## Key Directories

| Path | Purpose |
|------|---------|
| `backend/src/api/` | REST API endpoints |
| `backend/src/db/models.py` | Database models |
| `backend/src/services/` | Business logic |
| `frontend/src/pages/` | Page components |
| `frontend/src/components/` | Reusable components |
| `frontend/src/services/api.ts` | API client |

---

## Common Tasks

### Add New API Endpoint

1. Add schema in `backend/src/api/schemas.py`
2. Create router in `backend/src/api/`
3. Register in `backend/src/api/main.py`
4. Add method in `frontend/src/services/api.ts`

### Add New Page

1. Create page in `frontend/src/pages/NewPage.tsx`
2. Add route in `frontend/src/App.tsx`
3. Add navigation link

### Add New Database Table

1. Add model in `backend/src/db/models.py`
2. Restart backend (auto-creates tables)

---

## API Endpoints Overview

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/auth/register` | POST | No | Create account |
| `/api/v1/auth/login` | POST | No | Get JWT token |
| `/api/v1/agents` | GET | Yes | List agents |
| `/api/v1/agents` | POST | Yes | Create agent |
| `/api/v1/conversations` | GET | Yes | List chats |
| `/api/v1/conversations/{id}/messages` | POST | Yes | Send message |
| `/api/v1/approvals` | GET | Yes | Pending approvals |

---

## Architecture Summary

```
Frontend (React)  --HTTP-->  Backend (FastAPI)  -->  Database (SQLite)
     |                            |
     |                            +-->  MCP Server  -->  External APIs
     |                                    |
     +------------------------------------+
                  WebSocket (future)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| CORS error | Add frontend URL to `middleware.py` |
| Token expired | Logout and login again |
| Module not found | Check `PYTHONPATH` includes project root |
| Database error | Delete `backend/data/*.db` and restart |

---

## Next Steps

1. Read [TECHNICAL_GUIDE.md](./TECHNICAL_GUIDE.md) for full documentation
2. Explore the codebase starting with `backend/src/api/main.py`
3. Try creating an agent and starting a conversation
4. Check the approval center for pending actions
