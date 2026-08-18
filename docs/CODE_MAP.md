# Code Map - File Reference Guide

Quick reference for locating specific functionality in the codebase.

---

## Backend Files

### API Layer (`backend/src/api/`)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | FastAPI app setup | `app`, `lifespan()` |
| `auth.py` | Login/Register | `login()`, `register()` |
| `auth_utils.py` | JWT handling | `create_access_token()`, `get_current_active_user()` |
| `agents.py` | Agent CRUD | `list_agents()`, `create_agent()`, `update_agent()` |
| `conversations.py` | Chat endpoints | `send_message()`, `get_messages()` |
| `planning.py` | Workflow plans | `create_plan()`, `get_plan()` |
| `approvals.py` | Approval gates | `approve_request()`, `reject_request()` |
| `schemas.py` | Pydantic models | Request/Response validation |
| `middleware.py` | Security middleware | Rate limiting, headers, logging |

### Core Utilities (`backend/src/core/`)

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `config.py` | Environment vars | `JWT_SECRET`, `DATABASE_URL`, `GROQ_API_KEY` |
| `exceptions.py` | Error handling | `NotFoundError`, `ForbiddenError`, `raise_not_found()` |
| `security.py` | Security utils | `sanitize_string()`, `RateLimiter`, `validate_password_strength()` |
| `database.py` | DB helpers | `ResourceFetcher`, `TransactionManager` |

### Database (`backend/src/db/`)

| File | Purpose | Key Classes |
|------|---------|-------------|
| `models.py` | SQLAlchemy models | `User`, `Agent`, `Conversation`, `Message`, `ExecutionPlan`, `ApprovalRequest` |
| `connection.py` | DB connection | `get_db()`, `init_db()` |

### Services (`backend/src/services/`)

| File | Purpose | Key Classes |
|------|---------|-------------|
| `planning_service.py` | LangGraph workflows | `PlanningService.execute_planning_workflow()` |
| `approval_service.py` | Approval management | `ApprovalService.approve_request()` |
| `agent_executor.py` | Chat with agents | `AgentExecutor.process_message()` |

---

## Frontend Files

### Pages (`frontend/src/pages/`)

| File | Route | Purpose |
|------|-------|---------|
| `LoginPage.tsx` | `/login` | User login form |
| `RegisterPage.tsx` | `/register` | User registration |
| `DashboardPage.tsx` | `/` | Main dashboard |
| `ChatPage.tsx` | `/chat` | Chat interface |
| `ApprovalsPage.tsx` | `/approvals` | Approval center |

### Components (`frontend/src/components/`)

| Directory | Components | Purpose |
|-----------|------------|---------|
| `ui/` | Button, Card, Input, Label | Base UI components |
| `chat/` | MessageList, MessageInput, ConversationList | Chat interface |
| `agents/` | AgentSelector | Agent dropdown |
| `approvals/` | ApprovalCenter | Pending approvals UI |

### State & Services (`frontend/src/`)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `stores/authStore.ts` | Auth state | `useAuthStore` |
| `services/api.ts` | API client | `api` singleton |
| `hooks/useApi.ts` | Data fetching | `useApi()`, `useMutation()` |
| `hooks/useForm.ts` | Form handling | `useForm()`, `rules` |
| `lib/security.ts` | Token storage | `tokenStorage` |
| `lib/utils.ts` | Utilities | `cn()` |
| `types/index.ts` | TypeScript types | All interfaces |

---

## Key Data Types

### Backend Models (SQLAlchemy)

```python
User
├── id: int
├── email: str
├── password_hash: str
├── name: str
├── role: UserRole (ADMIN, USER)
├── organization_id: int
└── agents: List[Agent]

Agent
├── id: int
├── name: str
├── description: str
├── system_instructions: str
├── user_id: int
├── organization_id: int
└── tool_permissions: List[AgentToolPermission]

Conversation
├── id: int
├── title: str
├── user_id: int
├── agent_id: int
└── messages: List[Message]

Message
├── id: int
├── content: str
├── role: str (user, assistant)
└── conversation_id: int

ExecutionPlan
├── id: int
├── user_request: str
├── status: PlanStatus
├── plan_data: dict
├── current_step: int
└── approval_requests: List[ApprovalRequest]

ApprovalRequest
├── id: int
├── tool_name: str
├── tool_arguments: dict
├── status: ApprovalStatus (PENDING, APPROVED, REJECTED)
├── description: str
└── expires_at: datetime
```

### Frontend Types (TypeScript)

```typescript
interface User {
  id: number;
  email: string;
  name: string;
  role: "admin" | "user";
  organization_id: number;
}

interface Agent {
  id: number;
  name: string;
  description?: string;
  system_instructions?: string;
  tool_permissions: AgentToolPermission[];
}

interface Conversation {
  id: number;
  title?: string;
  agent_id: number;
  created_at: string;
}

interface Message {
  id: number;
  content: string;
  role: "user" | "assistant";
  conversation_id: number;
}
```

---

## Request Flow Examples

### Login Flow
```
LoginPage.tsx
  └── useAuthStore().login(credentials)
        └── api.login(credentials)
              └── POST /api/v1/auth/login
                    └── auth.py:login()
                          ├── Verify password
                          └── Return JWT token
```

### Send Message Flow
```
MessageInput.tsx
  └── api.sendMessage(conversationId, content)
        └── POST /api/v1/conversations/{id}/messages
              └── conversations.py:send_message()
                    ├── Save user message
                    ├── AgentExecutor.process_message()
                    │     ├── Load agent config
                    │     ├── Call LLM
                    │     └── Execute tools
                    └── Save AI response
```

### Approval Flow
```
ApprovalCenter.tsx
  └── api.approveRequest(approvalId)
        └── POST /api/v1/approvals/{id}/approve
              └── approvals.py:approve()
                    └── ApprovalService.approve_request()
                          ├── Update status to APPROVED
                          └── Execute approved tool
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (API keys, secrets) |
| `backend/requirements.txt` | Python dependencies |
| `frontend/package.json` | Node dependencies |
| `frontend/vite.config.ts` | Vite build config |
| `frontend/tsconfig.json` | TypeScript config |
| `docker-compose.yml` | Container orchestration |
| `backend/Dockerfile` | Backend container |
| `frontend/Dockerfile` | Frontend container |
| `frontend/nginx.conf` | Production nginx config |

---

## Adding New Features Checklist

### New API Endpoint
- [ ] Add Pydantic schema in `schemas.py`
- [ ] Create router file in `backend/src/api/`
- [ ] Register router in `main.py`
- [ ] Add TypeScript type in `types/index.ts`
- [ ] Add API method in `api.ts`

### New Database Table
- [ ] Add SQLAlchemy model in `models.py`
- [ ] Add relationships to existing models
- [ ] Restart backend (auto-creates table)

### New Frontend Page
- [ ] Create page component in `pages/`
- [ ] Add route in `App.tsx`
- [ ] Add to navigation (if needed)

### New React Component
- [ ] Create component file
- [ ] Add to barrel export if reusable
- [ ] Document props with TypeScript
