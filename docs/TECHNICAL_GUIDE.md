# AI Workforce Platform - Technical Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Backend Deep Dive](#backend-deep-dive)
6. [Frontend Deep Dive](#frontend-deep-dive)
7. [Authentication Flow](#authentication-flow)
8. [Data Flow](#data-flow)
9. [Security Implementation](#security-implementation)
10. [Development Guide](#development-guide)
11. [API Reference](#api-reference)
12. [Database Schema](#database-schema)
13. [Troubleshooting](#troubleshooting)

---

## Project Overview

The AI Workforce Platform is a multi-agent AI system that enables users to create, manage, and interact with AI assistants. Key features include:

- **Multi-Agent Workspace**: Create specialized AI assistants with custom tool permissions
- **Planning Workflows**: LangGraph-based multi-step execution plans with approval gates
- **Conversation Management**: Persistent chat history with AI agents
- **Human Approval Gates**: Sensitive actions require user approval before execution
- **Meeting Delegation** (planned): AI auto-joins meetings based on importance
- **Interview Automation** (planned): AI-conducted interviews with scoring

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  React + TypeScript + Vite (Port 5173/3000)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Pages     │  │ Components  │  │   Stores    │              │
│  │  - Login    │  │  - Chat     │  │  - Auth     │              │
│  │  - Chat     │  │  - Agents   │  │             │              │
│  │  - Approvals│  │  - Approvals│  │             │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                          │                                       │
│                    API Client (axios)                            │
└──────────────────────────┼──────────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API                                   │
│  FastAPI + SQLAlchemy (Port 8001)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Routers   │  │  Services   │  │   Models    │              │
│  │  /auth      │  │  Planning   │  │  User       │              │
│  │  /agents    │  │  Approval   │  │  Agent      │              │
│  │  /convos    │  │  Agent Exec │  │  Convo      │              │
│  │  /planning  │  │             │  │  Message    │              │
│  │  /approvals │  │             │  │  Plan       │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                          │                                       │
│              ┌───────────┴───────────┐                          │
│              ▼                       ▼                          │
│      ┌─────────────┐         ┌─────────────┐                    │
│      │  SQLite DB  │         │  MCP Server │                    │
│      │  (SQLAlchemy)│         │  (Port 8000)│                    │
│      └─────────────┘         └─────────────┘                    │
│                                     │                            │
│                              External APIs                       │
│                         (Nylas, Groq, Weather)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| Frontend | User interface, authentication, API communication |
| Backend API | Business logic, data persistence, user management |
| MCP Server | Tool execution, external API integration |
| Database | Persistent storage for users, agents, conversations |

---

## Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Runtime |
| FastAPI | REST API framework |
| SQLAlchemy | ORM for database |
| Pydantic | Data validation |
| LangGraph | Planning workflow orchestration |
| LangChain + Groq | LLM integration |
| JWT (PyJWT) | Authentication tokens |
| Passlib + bcrypt | Password hashing |

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool |
| Zustand | State management |
| Axios | HTTP client |
| Tailwind CSS | Styling |
| React Router | Navigation |

### External Services
| Service | Purpose |
|---------|---------|
| Nylas | Calendar, email, meeting notetaker |
| Groq | LLM API (Llama 3.3) |
| WeatherAPI | Weather data |

---

## Project Structure

```
mcp/
├── backend/                    # Backend Python application
│   ├── src/
│   │   ├── api/               # FastAPI routers and endpoints
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── auth_utils.py  # JWT utilities
│   │   │   ├── agents.py      # Agent CRUD endpoints
│   │   │   ├── conversations.py # Chat endpoints
│   │   │   ├── planning.py    # Planning workflow endpoints
│   │   │   ├── approvals.py   # Approval gate endpoints
│   │   │   ├── schemas.py     # Pydantic schemas
│   │   │   ├── middleware.py  # Security middleware
│   │   │   └── main.py        # FastAPI app entry point
│   │   ├── core/              # Core utilities
│   │   │   ├── config.py      # Environment configuration
│   │   │   ├── exceptions.py  # Custom exceptions
│   │   │   ├── security.py    # Security utilities
│   │   │   └── database.py    # Database helpers
│   │   ├── db/                # Database layer
│   │   │   ├── models.py      # SQLAlchemy models
│   │   │   └── connection.py  # Database connection
│   │   ├── services/          # Business logic
│   │   │   ├── planning_service.py  # LangGraph workflows
│   │   │   ├── approval_service.py  # Approval management
│   │   │   └── agent_executor.py    # Agent chat logic
│   │   └── mcp/               # MCP server tools
│   │       └── tools/         # Tool implementations
│   ├── main.py                # Backend entry point
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Container config
├── frontend/                  # Frontend React application
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ui/           # Base UI components
│   │   │   ├── chat/         # Chat-related components
│   │   │   ├── agents/       # Agent management
│   │   │   └── approvals/    # Approval center
│   │   ├── pages/            # Page components
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   └── ApprovalsPage.tsx
│   │   ├── stores/           # Zustand stores
│   │   │   └── authStore.ts  # Authentication state
│   │   ├── services/         # API communication
│   │   │   └── api.ts        # API client
│   │   ├── hooks/            # Custom React hooks
│   │   │   ├── useApi.ts     # Data fetching hooks
│   │   │   └── useForm.ts    # Form handling hooks
│   │   ├── lib/              # Utilities
│   │   │   ├── utils.ts      # General utilities
│   │   │   └── security.ts   # Security utilities
│   │   ├── types/            # TypeScript types
│   │   │   └── index.ts      # Type definitions
│   │   ├── App.tsx           # Root component
│   │   └── main.tsx          # Entry point
│   ├── package.json          # Node dependencies
│   ├── vite.config.ts        # Vite configuration
│   ├── nginx.conf            # Production nginx config
│   └── Dockerfile            # Container config
├── docker-compose.yml         # Docker orchestration
├── .env.example              # Environment template
└── docs/                     # Documentation
    └── TECHNICAL_GUIDE.md    # This file
```

---

## Backend Deep Dive

### Entry Point Flow

```
backend/main.py
    │
    ├── Starts MCP Server (port 8000)
    │   └── Exposes tools: calendar, email, notetaker, weather
    │
    └── Starts FastAPI Server (port 8001)
        └── backend/src/api/main.py
            ├── Initializes database
            ├── Sets up middleware (security, rate limiting, logging)
            └── Mounts routers (/auth, /agents, /conversations, etc.)
```

### API Router Structure

Each router follows a consistent pattern:

```python
# backend/src/api/agents.py

from fastapi import APIRouter, Depends, status
from backend.src.api.auth_utils import get_current_active_user
from backend.src.core.database import ResourceFetcher

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("")
def list_agents(
    current_user: User = Depends(get_current_active_user),  # Auth required
    db: Session = Depends(get_db)                           # DB session
):
    fetcher = ResourceFetcher(db, Agent, "Agent")
    agents = fetcher.list_for_organization(current_user.organization_id)
    return [AgentResponse.model_validate(agent) for agent in agents]
```

### Key Patterns

#### 1. Dependency Injection
FastAPI uses `Depends()` for injecting:
- `get_db()` → Database session
- `get_current_active_user()` → Authenticated user

```python
@router.get("/protected")
def protected_route(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # current_user is guaranteed to be authenticated
    # db is a SQLAlchemy session
    pass
```

#### 2. Resource Fetcher Pattern
Eliminates duplicated ownership checks:

```python
# Instead of this (repeated in every endpoint):
agent = db.query(Agent).filter(
    Agent.id == agent_id,
    Agent.organization_id == current_user.organization_id
).first()
if not agent:
    raise HTTPException(404, "Agent not found")

# Use this:
fetcher = ResourceFetcher(db, Agent, "Agent")
agent = fetcher.get_for_user_and_org(agent_id, user_id, org_id)
```

#### 3. Pydantic Schema Validation
Request/response validation with custom validators:

```python
# backend/src/api/schemas.py

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError("Must contain uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Must contain lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Must contain digit")
        return v
```

### Database Models

Located in `backend/src/db/models.py`:

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Relationships
    organization = relationship("Organization", back_populates="users")
    agents = relationship("Agent", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
```

### Services Layer

Business logic is separated into services:

```python
# backend/src/services/planning_service.py

class PlanningService:
    def __init__(self, db: Session):
        self.db = db
        self.approval_service = ApprovalService(db)
        self.llm = ChatGroq(api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")

    async def execute_planning_workflow(
        self,
        conversation_id: int,
        user_id: int,
        agent_id: int,
        user_request: str
    ) -> ExecutionPlan:
        # Creates LangGraph workflow
        # Executes analyze → plan → validate → execute → synthesize
        pass
```

### LangGraph Planning Workflow

```
┌─────────────┐
│   ANALYZE   │  Extract intent from user request
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    PLAN     │  Create step-by-step execution plan
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  VALIDATE   │  Check tool permissions, mark approval gates
└──────┬──────┘
       │
       ▼
┌─────────────┐
│EXECUTE_STEP │◄─────┐  Execute current step
└──────┬──────┘      │
       │             │
       ▼             │
┌─────────────┐      │
│CHECK_APPROVAL│     │  Wait for approval if needed
└──────┬──────┘      │
       │             │
       ├─────────────┘  (loop until all steps done)
       │
       ▼
┌─────────────┐
│ SYNTHESIZE  │  Summarize results
└─────────────┘
```

---

## Frontend Deep Dive

### Entry Point Flow

```
frontend/src/main.tsx
    │
    └── <App />
        │
        └── <BrowserRouter>
            │
            ├── <Route path="/login" element={<LoginPage />} />
            ├── <Route path="/register" element={<RegisterPage />} />
            └── <Route element={<ProtectedRoute />}>
                ├── <Route path="/" element={<DashboardPage />} />
                ├── <Route path="/chat" element={<ChatPage />} />
                └── <Route path="/approvals" element={<ApprovalsPage />} />
```

### State Management (Zustand)

```typescript
// frontend/src/stores/authStore.ts

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,

      login: async (credentials) => {
        const response = await api.login(credentials);
        set({ user: response.user, isAuthenticated: true });
      },

      logout: () => {
        tokenStorage.clearToken();
        set({ user: null, isAuthenticated: false });
      },
    }),
    { name: "auth-storage" }
  )
);

// Usage in components:
function LoginPage() {
  const { login, isLoading, error } = useAuthStore();

  const handleSubmit = async (data) => {
    await login(data);
    navigate("/");
  };
}
```

### API Client Pattern

```typescript
// frontend/src/services/api.ts

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000,
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = tokenStorage.getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle 401 errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          tokenStorage.clearToken();
          window.location.href = "/login";
        }
        throw error;
      }
    );
  }

  async getAgents(): Promise<Agent[]> {
    return this.requestWithRetry({ method: "GET", url: "/agents" });
  }
}

export const api = new ApiClient();
```

### Custom Hooks

#### useApi Hook
```typescript
// frontend/src/hooks/useApi.ts

const { data, error, isLoading, execute } = useApi(
  () => api.getAgents(),
  { cacheKey: 'agents', retries: 3 }
);

// In component:
useEffect(() => {
  execute();
}, []);

if (isLoading) return <Spinner />;
if (error) return <Error message={error} />;
return <AgentList agents={data} />;
```

#### useForm Hook
```typescript
// frontend/src/hooks/useForm.ts

const { values, errors, handleChange, handleSubmit } = useForm(
  {
    email: {
      initialValue: '',
      rules: [rules.required(), rules.email()]
    },
    password: {
      initialValue: '',
      rules: [rules.required(), rules.password()]
    }
  },
  async (data) => {
    await api.login(data);
    navigate("/");
  }
);

return (
  <form onSubmit={handleSubmit}>
    <input
      name="email"
      value={values.email}
      onChange={handleChange}
    />
    {errors.email && <span>{errors.email}</span>}
  </form>
);
```

### Component Structure

```
ChatPage.tsx
├── AgentSelector          # Dropdown to select agent
├── ConversationList       # Sidebar with conversation history
├── MessageList            # Chat message display
│   ├── MessageBubble      # Individual message
│   └── ToolExecutionCard  # Tool call visualization
└── MessageInput           # Text input + send button
```

---

## Authentication Flow

### Registration Flow

```
┌──────────┐     POST /auth/register      ┌──────────┐
│ Frontend │ ────────────────────────────► │ Backend  │
│          │  { email, name, password }   │          │
└──────────┘                               └────┬─────┘
                                                │
                                    1. Validate input
                                    2. Check email unique
                                    3. Hash password
                                    4. Create organization
                                    5. Create user
                                    6. Generate JWT
                                                │
┌──────────┐     { access_token, user }    ┌────▼─────┐
│ Frontend │ ◄──────────────────────────── │ Backend  │
│          │                               │          │
└────┬─────┘                               └──────────┘
     │
     │  Store token in sessionStorage
     │  Store user in Zustand state
     ▼
┌──────────┐
│ Redirect │
│ to /     │
└──────────┘
```

### Login Flow

```
┌──────────┐     POST /auth/login         ┌──────────┐
│ Frontend │ ────────────────────────────► │ Backend  │
│          │  { email, password }         │          │
└──────────┘                               └────┬─────┘
                                                │
                                    1. Find user by email
                                    2. Verify password hash
                                    3. Generate JWT token
                                                │
┌──────────┐     { access_token, user }    ┌────▼─────┐
│ Frontend │ ◄──────────────────────────── │ Backend  │
└────┬─────┘                               └──────────┘
     │
     │  tokenStorage.setToken(token)
     │  authStore.set({ user, isAuthenticated: true })
     ▼
```

### Protected Route Check

```typescript
// frontend/src/components/ProtectedRoute.tsx

function ProtectedRoute() {
  const { isAuthenticated, checkAuth } = useAuthStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    checkAuth().finally(() => setChecking(false));
  }, []);

  if (checking) return <LoadingScreen />;
  if (!isAuthenticated) return <Navigate to="/login" />;
  return <Outlet />;
}
```

### JWT Token Structure

```json
{
  "sub": "user@example.com",    // Subject (user identifier)
  "user_id": 1,                  // User ID
  "exp": 1234567890,             // Expiration timestamp
  "iat": 1234567890              // Issued at timestamp
}
```

---

## Data Flow

### Chat Message Flow

```
User types message
        │
        ▼
┌─────────────────┐
│  MessageInput   │  1. Capture input
│                 │  2. Clear input field
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   api.ts        │  POST /conversations/{id}/messages
│  sendMessage()  │  { content: "Hello" }
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  conversations  │  1. Verify user owns conversation
│    .py          │  2. Save user message to DB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AgentExecutor   │  1. Load agent config
│                 │  2. Filter tools by permissions
│                 │  3. Call LLM with context
│                 │  4. Execute tool calls
│                 │  5. Return AI response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  conversations  │  1. Save AI message to DB
│    .py          │  2. Return message response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend       │  1. Add message to UI
│                 │  2. Scroll to bottom
└─────────────────┘
```

### Planning Workflow Data Flow

```
User: "Schedule a meeting and send invites"
        │
        ▼
┌─────────────────────────────────────────────────┐
│  PlanningService.execute_planning_workflow()     │
│                                                  │
│  State Machine:                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ analyze_request()                         │   │
│  │ → "User wants to schedule meeting"        │   │
│  └─────────────┬────────────────────────────┘   │
│                │                                 │
│  ┌─────────────▼────────────────────────────┐   │
│  │ create_plan()                             │   │
│  │ → [                                       │   │
│  │     {step: 1, tool: "get_current_datetime"},│ │
│  │     {step: 2, tool: "create_calendar_event",│ │
│  │      requires_approval: true},              │ │
│  │     {step: 3, tool: "send_email",          │ │
│  │      requires_approval: true}               │ │
│  │   ]                                        │   │
│  └─────────────┬────────────────────────────┘   │
│                │                                 │
│  ┌─────────────▼────────────────────────────┐   │
│  │ validate_plan()                           │   │
│  │ → Check tool permissions                  │   │
│  │ → Mark approval requirements              │   │
│  └─────────────┬────────────────────────────┘   │
│                │                                 │
│  ┌─────────────▼────────────────────────────┐   │
│  │ execute_step() (loop)                     │   │
│  │ → If requires_approval:                   │   │
│  │     Create ApprovalRequest                │   │
│  │     Pause execution                       │   │
│  │ → Else:                                   │   │
│  │     Execute tool                          │   │
│  │     Store result                          │   │
│  └─────────────┬────────────────────────────┘   │
│                │                                 │
│  ┌─────────────▼────────────────────────────┐   │
│  │ synthesize_results()                      │   │
│  │ → "Meeting scheduled for 2pm. Invites    │   │
│  │    sent to john@example.com"              │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Security Implementation

### Backend Security Layers

```
Request
   │
   ▼
┌─────────────────────────┐
│ InputValidationMiddleware│  Detect injection patterns
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   RateLimitMiddleware   │  100 req/min (unauthenticated)
│                         │  300 req/min (authenticated)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ RequestLoggingMiddleware│  Log all requests
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│SecurityHeadersMiddleware│  X-Frame-Options, CSP, etc.
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│     CORS Middleware     │  Allow specific origins
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   JWT Authentication    │  Verify token, load user
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Pydantic Validation   │  Schema validation
└───────────┬─────────────┘
            │
            ▼
      Route Handler
```

### Password Security

```python
# backend/src/api/auth_utils.py

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### Token Security (Frontend)

```typescript
// frontend/src/lib/security.ts

// Memory-first storage (more secure than localStorage)
let inMemoryToken: string | null = null;

export const tokenStorage = {
  getToken(): string | null {
    // Prefer in-memory (cleared on page close)
    if (inMemoryToken) return inMemoryToken;

    // Fallback to sessionStorage (cleared on tab close)
    const stored = sessionStorage.getItem("access_token");
    if (stored) {
      inMemoryToken = stored;
      return stored;
    }

    // Migrate from localStorage if present (legacy cleanup)
    const legacy = localStorage.getItem("access_token");
    if (legacy) {
      this.setToken(legacy);
      localStorage.removeItem("access_token");
      return legacy;
    }

    return null;
  },

  setToken(token: string): void {
    inMemoryToken = token;
    sessionStorage.setItem("access_token", token);
  },

  clearToken(): void {
    inMemoryToken = null;
    sessionStorage.removeItem("access_token");
  },

  isTokenExpired(): boolean {
    const token = this.getToken();
    if (!token) return true;

    const payload = this.parseToken(token);
    const now = Math.floor(Date.now() / 1000);
    return payload.exp < now + 30; // 30 second buffer
  }
};
```

---

## Development Guide

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Environment Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd mcp
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Backend setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

4. **Frontend setup**
```bash
cd frontend
npm install
```

### Running Locally

**Terminal 1 - Backend:**
```bash
cd backend
python -m backend.main
# Backend runs on http://localhost:8001
# MCP server runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

### Docker Deployment

```bash
docker-compose up --build
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
```

### Adding a New API Endpoint

1. **Create schema** in `backend/src/api/schemas.py`:
```python
class NewFeatureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
```

2. **Create model** in `backend/src/db/models.py`:
```python
class NewFeature(Base):
    __tablename__ = "new_features"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
```

3. **Create router** in `backend/src/api/new_feature.py`:
```python
router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("", response_model=NewFeatureResponse)
def create_new_feature(
    data: NewFeatureCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    feature = NewFeature(name=data.name)
    db.add(feature)
    db.commit()
    return feature
```

4. **Register router** in `backend/src/api/main.py`:
```python
from backend.src.api.new_feature import router as new_feature_router
app.include_router(new_feature_router, prefix="/api/v1")
```

5. **Add frontend API method** in `frontend/src/services/api.ts`:
```typescript
async createNewFeature(data: NewFeatureCreate): Promise<NewFeature> {
  const response = await this.client.post<NewFeature>("/new-feature", data);
  return response.data;
}
```

---

## API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login and get token |
| `/api/v1/auth/me` | GET | Get current user |

### Agents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/agents` | GET | List all agents |
| `/api/v1/agents` | POST | Create agent |
| `/api/v1/agents/{id}` | GET | Get agent by ID |
| `/api/v1/agents/{id}` | PUT | Update agent |
| `/api/v1/agents/{id}` | DELETE | Delete agent |

### Conversations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/conversations` | GET | List conversations |
| `/api/v1/conversations` | POST | Create conversation |
| `/api/v1/conversations/{id}` | GET | Get conversation |
| `/api/v1/conversations/{id}` | DELETE | Delete conversation |
| `/api/v1/conversations/{id}/messages` | GET | Get messages |
| `/api/v1/conversations/{id}/messages` | POST | Send message |

### Planning

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/planning` | POST | Create execution plan |
| `/api/v1/planning/{id}` | GET | Get plan status |
| `/api/v1/planning/{id}/cancel` | POST | Cancel plan |
| `/api/v1/planning/conversation/{id}` | GET | Get plans for conversation |

### Approvals

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/approvals` | GET | Get pending approvals |
| `/api/v1/approvals/{id}` | GET | Get approval details |
| `/api/v1/approvals/{id}/approve` | POST | Approve request |
| `/api/v1/approvals/{id}/reject` | POST | Reject request |

---

## Database Schema

```
┌─────────────────┐       ┌─────────────────┐
│  organizations  │       │     users       │
├─────────────────┤       ├─────────────────┤
│ id              │◄──┐   │ id              │
│ name            │   │   │ email           │
│ plan_type       │   │   │ password_hash   │
│ created_at      │   │   │ name            │
└─────────────────┘   │   │ role            │
                      └───│ organization_id │
                          │ created_at      │
                          └────────┬────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     agents      │       │ conversations   │       │ execution_plans │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id              │◄──┐   │ id              │◄──┐   │ id              │
│ name            │   │   │ title           │   │   │ user_request    │
│ description     │   │   │ user_id         │───┘   │ status          │
│ system_instruct │   │   │ agent_id        │───┐   │ plan_data       │
│ user_id         │───┘   │ created_at      │   │   │ conversation_id │
│ organization_id │       │ updated_at      │   │   │ user_id         │
│ created_at      │       └────────┬────────┘   │   │ agent_id        │
└────────┬────────┘                │            │   │ created_at      │
         │                         │            │   └─────────────────┘
         │                         ▼            │
         │                ┌─────────────────┐   │
         │                │    messages     │   │
         │                ├─────────────────┤   │
         │                │ id              │   │
         │                │ content         │   │
         │                │ role            │   │
         │                │ conversation_id │───┘
         │                │ created_at      │
         │                └─────────────────┘
         │
         ▼
┌─────────────────────────┐       ┌─────────────────┐
│ agent_tool_permissions  │       │approval_requests│
├─────────────────────────┤       ├─────────────────┤
│ id                      │       │ id              │
│ agent_id                │       │ tool_name       │
│ tool_name               │       │ tool_arguments  │
│ permission_level        │       │ description     │
└─────────────────────────┘       │ status          │
                                  │ user_id         │
                                  │ agent_id        │
                                  │ execution_plan_id│
                                  │ expires_at      │
                                  └─────────────────┘
```

---

## Troubleshooting

### Common Issues

#### 1. "Token expired" error
**Cause**: JWT token has expired (default: 7 days)
**Solution**: Log out and log in again

#### 2. CORS errors
**Cause**: Frontend URL not in allowed origins
**Solution**: Add URL to `backend/src/api/middleware.py`:
```python
allow_origins=[
    "http://localhost:5173",
    "http://your-new-url.com",
]
```

#### 3. "Agent not found" when accessing agents
**Cause**: Agent belongs to different organization
**Solution**: Agents are organization-scoped. Ensure you're logged in as a user in the same organization.

#### 4. Database not initializing
**Cause**: Database file permissions or path issue
**Solution**:
```bash
mkdir -p backend/data
chmod 755 backend/data
```

#### 5. "Module not found" errors
**Cause**: Python path not configured
**Solution**: Ensure `PYTHONPATH` includes project root:
```bash
export PYTHONPATH=/path/to/mcp:$PYTHONPATH
```

### Debug Mode

**Backend**: Set `LOG_LEVEL=DEBUG` in `.env`

**Frontend**: Check browser DevTools console

### Health Checks

- Backend: `GET http://localhost:8001/health`
- Frontend: `GET http://localhost:5173/`

---

## Contributing

1. Create a feature branch from `main`
2. Follow the existing code patterns
3. Add tests for new features
4. Update documentation
5. Submit a pull request

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, prefer `type` over `interface`
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

---

## License

[Add your license here]

---

*Last updated: 2026-08-19*
