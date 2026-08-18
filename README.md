# AI Workforce Platform

A comprehensive AI-powered workforce automation platform featuring multi-agent chat, meeting delegation, planning workflows with human approval gates, and more.

## Project Structure

```
ai-workforce-platform/
├── backend/                    # Python Backend
│   ├── src/
│   │   ├── api/               # FastAPI routes (auth, agents, conversations, planning, approvals)
│   │   ├── core/              # Configuration, dependencies
│   │   ├── db/                # Database models and connection (SQLAlchemy)
│   │   ├── services/          # Business logic services
│   │   └── mcp/               # MCP server and tools
│   ├── scripts/               # Database seeding, migrations
│   ├── tests/                 # Backend tests
│   ├── data/                  # SQLite database (gitignored)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py                # Backend entry point
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client
│   │   ├── stores/            # Zustand state management
│   │   ├── types/             # TypeScript types
│   │   └── lib/               # Utilities
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
│
├── docs/                       # Documentation
├── scripts/                    # Development scripts
├── docker-compose.yml          # Docker orchestration
├── .env.example               # Environment template
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm or yarn

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd ai-workforce-platform

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Seed the database
python -m backend.scripts.seed

# Run backend server
python -m backend.main
```

Backend runs on: http://localhost:8001
API Docs: http://localhost:8001/docs

### 3. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs on: http://localhost:5173

### 4. Default Login

- **Email:** admin@example.com
- **Password:** admin123

## Docker Deployment

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Ports:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- MCP Server: http://localhost:8000

## Features

### Phase 1: Foundation (Completed)
- MCP server with tools (calendar, email, weather, meetings)
- Nylas integration for calendar and email
- Meeting notetaker with transcription

### Phase 2: Multi-Agent Chat (Completed)
- User authentication (JWT)
- Agent management with tool permissions
- Persistent conversation history
- React chat interface

### Phase 3: Planning & Approval (Completed)
- LangGraph-based planning workflows
- Human approval gates for sensitive actions
- Approval center UI
- Multi-step plan execution

### Phase 4-8: (Coming Soon)
- Meeting delegation
- Team collaboration
- Analytics dashboard
- WebSocket real-time updates

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Current user

### Agents
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Create agent
- `PUT /api/v1/agents/{id}` - Update agent
- `DELETE /api/v1/agents/{id}` - Delete agent

### Conversations
- `GET /api/v1/conversations` - List conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{id}/messages` - Get messages
- `POST /api/v1/conversations/{id}/messages` - Send message

### Planning
- `POST /api/v1/planning` - Create execution plan
- `GET /api/v1/planning/{id}` - Get plan status
- `POST /api/v1/planning/{id}/cancel` - Cancel plan

### Approvals
- `GET /api/v1/approvals` - List pending approvals
- `POST /api/v1/approvals/{id}/approve` - Approve request
- `POST /api/v1/approvals/{id}/reject` - Reject request

## Environment Variables

See `.env.example` for all available configuration options.

**Required:**
- `JWT_SECRET` - Secret key for JWT tokens
- `GROQ_API_KEY` - Groq API key for LLM

**Optional:**
- `NYLAS_API_KEY` / `NYLAS_GRANT_ID` - For calendar/email features
- `WEATHER_API_KEY` - For weather tool

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Structure

**Backend:**
- `src/api/` - FastAPI route handlers
- `src/services/` - Business logic (AgentExecutor, PlanningService, ApprovalService)
- `src/db/` - SQLAlchemy models and database connection
- `src/core/` - Configuration and dependencies

**Frontend:**
- `src/components/` - Reusable React components
- `src/pages/` - Page-level components
- `src/services/api.ts` - Axios API client
- `src/stores/` - Zustand state stores
- `src/types/` - TypeScript interfaces

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
