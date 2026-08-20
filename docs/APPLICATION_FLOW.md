# AI Workforce Platform - Application Flow Documentation

## Table of Contents
1. [System Architecture Overview](#1-system-architecture-overview)
2. [User Authentication Flow](#2-user-authentication-flow)
3. [Multi-Agent Chat Flow](#3-multi-agent-chat-flow)
4. [Planning & Approval Flow](#4-planning--approval-flow)
5. [Meeting Delegation Flow](#5-meeting-delegation-flow)
6. [AI Interview Flow](#6-ai-interview-flow)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [API Integration Flow](#8-api-integration-flow)

---

## 1. System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    React Frontend (Port 3000)                        │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │Dashboard │ │  Chat    │ │Delegation│ │Interview │ │Approvals │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP/REST API
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   FastAPI Backend (Port 8000)                        │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │  Auth    │ │  Agents  │ │Delegation│ │Interview │ │ Planning │   │    │
│  │  │  API     │ │   API    │ │   API    │ │   API    │ │   API    │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Agent   │ │Delegation│ │Interview │ │ Calendar │ │ Notetaker│          │
│  │ Executor │ │ Service  │ │ Service  │ │ Service  │ │ Service  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────┐ ┌─────────────────┐ ┌─────────────────────────────┐
│      DATA LAYER         │ │  EXTERNAL APIs  │ │       AI SERVICES           │
│  ┌─────────────────┐    │ │  ┌───────────┐  │ │  ┌─────────────────────┐    │
│  │   PostgreSQL    │    │ │  │   Nylas   │  │ │  │   Groq LLM API      │    │
│  │   (AI_Workforce)│    │ │  │  Calendar │  │ │  │   (llama-3.3-70b)   │    │
│  └─────────────────┘    │ │  │   Email   │  │ │  └─────────────────────┘    │
│  ┌─────────────────┐    │ │  │  Notetaker│  │ │  ┌─────────────────────┐    │
│  │     Redis       │    │ │  └───────────┘  │ │  │   TTS Service       │    │
│  │    (Cache)      │    │ │                 │ │  │   (gTTS/ElevenLabs) │    │
│  └─────────────────┘    │ │                 │ │  └─────────────────────┘    │
└─────────────────────────┘ └─────────────────┘ └─────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 19 + TypeScript | User Interface |
| State Management | Zustand | Client-side state |
| API Client | Axios | HTTP requests |
| Backend | FastAPI (Python) | REST API server |
| Database | PostgreSQL 15 | Persistent storage |
| Cache | Redis 7 | Session & rate limiting |
| AI/LLM | Groq (llama-3.3-70b) | Natural language processing |
| Calendar/Email | Nylas API | Calendar & email integration |
| TTS | gTTS / ElevenLabs | Text-to-Speech for AI speaking |

---

## 2. User Authentication Flow

### Registration Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │     │ Frontend │     │  Auth    │     │ Database │     │   JWT    │
│          │     │          │     │   API    │     │          │     │  Token   │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Fill Form   │                │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2. POST /auth/register          │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 3. Check email │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 4. Hash password               │
     │                │                │────────────────────────────────>│
     │                │                │                │                │
     │                │                │ 5. Create Organization (if new) │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 6. Create User │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 7. Generate JWT│                │
     │                │                │────────────────────────────────>│
     │                │                │                │                │
     │                │ 8. Return token + user          │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 9. Store token │                │                │                │
     │<───────────────│                │                │                │
     │                │                │                │                │
     │ 10. Redirect to Dashboard       │                │                │
     │<───────────────│                │                │                │
```

### Login Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │     │ Frontend │     │  Auth    │     │ Database │
│          │     │          │     │   API    │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. Enter credentials            │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ 2. POST /auth/login             │
     │                │───────────────>│                │
     │                │                │                │
     │                │                │ 3. Find user   │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 4. Verify password (bcrypt)
     │                │                │────────────────│
     │                │                │                │
     │                │                │ 5. Generate JWT token
     │                │                │────────────────│
     │                │                │                │
     │                │ 6. Return {access_token, user}  │
     │                │<───────────────│                │
     │                │                │                │
     │ 7. Store in localStorage        │                │
     │<───────────────│                │                │
     │                │                │                │
     │ 8. Redirect to Dashboard        │                │
     │<───────────────│                │                │
```

### Token Validation (Every Request)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │     │   API    │     │   JWT    │     │ Database │
│          │     │ Middleware│    │ Validator│     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. Request with Bearer token    │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ 2. Extract token               │
     │                │───────────────>│                │
     │                │                │                │
     │                │ 3. Verify signature & expiry   │
     │                │                │────────────────│
     │                │                │                │
     │                │ 4. Get user from DB            │
     │                │                │───────────────>│
     │                │                │                │
     │                │ 5. Inject user into request    │
     │                │<───────────────│                │
     │                │                │                │
     │ 6. Process request              │                │
     │<───────────────│                │                │
```

---

## 3. Multi-Agent Chat Flow

### Agent Creation Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   User   │     │ Frontend │     │ Agents   │     │ Database │
│          │     │          │     │   API    │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. Click "Create Agent"         │                │
     │───────────────>│                │                │
     │                │                │                │
     │ 2. Fill agent details           │                │
     │   - Name                        │                │
     │   - Description                 │                │
     │   - System Instructions         │                │
     │   - Tool Permissions            │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ 3. POST /agents                 │
     │                │───────────────>│                │
     │                │                │                │
     │                │                │ 4. Create Agent│
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 5. Create Tool Permissions
     │                │                │───────────────>│
     │                │                │                │
     │                │ 6. Return agent                 │
     │                │<───────────────│                │
     │                │                │                │
     │ 7. Show in agent list           │                │
     │<───────────────│                │                │
```

### Conversation Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   User   │     │ Frontend │     │  Chat    │     │  Agent   │     │   LLM    │
│          │     │          │     │   API    │     │ Executor │     │  (Groq)  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Select Agent│                │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2. POST /conversations          │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │ 3. Create conversation          │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 4. Type message│                │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 5. POST /conversations/{id}/messages             │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 6. Load agent config            │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 7. Filter tools by permissions  │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 8. Build prompt with context    │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │                │ 9. Call LLM   │
     │                │                │                │───────────────>│
     │                │                │                │                │
     │                │                │                │ 10. AI Response│
     │                │                │                │<───────────────│
     │                │                │                │                │
     │                │                │ 11. Save messages               │
     │                │                │<───────────────│                │
     │                │                │                │                │
     │                │ 12. Return response             │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 13. Display    │                │                │                │
     │<───────────────│                │                │                │
```

### Tool Execution Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   LLM    │     │  Agent   │     │  Tool    │     │ External │     │ Database │
│          │     │ Executor │     │ Handler  │     │   API    │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Tool call request            │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2. Check permission             │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 3. If REQUIRES_APPROVAL         │
     │                │                │───────────────────────────────>│
     │                │                │    Create ApprovalRequest       │
     │                │                │                │                │
     │                │                │ 4. If ENABLED │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 5. Execute tool│                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 6. Return result                │
     │                │                │<───────────────│                │
     │                │                │                │                │
     │                │ 7. Format result               │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 8. Continue generation          │                │                │
     │<───────────────│                │                │                │
```

---

## 4. Planning & Approval Flow

### Plan Creation Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   User   │     │ Frontend │     │ Planning │     │ LangGraph│     │   LLM    │
│          │     │          │     │   API    │     │ Planner  │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Enable "Planning Mode"       │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │ 2. Send complex request         │                │                │
     │   "Schedule meeting and         │                │                │
     │    send invites to team"        │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 3. POST /planning               │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 4. Initialize state machine     │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │                │ 5. Analyze    │
     │                │                │                │───────────────>│
     │                │                │                │                │
     │                │                │                │ 6. Generate plan
     │                │                │                │<───────────────│
     │                │                │                │                │
     │                │                │ 7. Return plan with steps       │
     │                │                │<───────────────│                │
     │                │                │                │                │
     │                │ 8. Show plan visualization      │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 9. Display plan│                │                │                │
     │   (ReactFlow)  │                │                │                │
     │<───────────────│                │                │                │
```

### Plan Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXECUTION PLAN                                     │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Step 1    │───>│   Step 2    │───>│   Step 3    │───>│   Step 4    │   │
│  │  Get Date   │    │  Check      │    │  Create     │    │  Get Link   │   │
│  │             │    │  Calendar   │    │  Meeting    │    │             │   │
│  │ [PENDING]   │    │ [PENDING]   │    │ [APPROVAL]  │    │ [PENDING]   │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│                                              │                               │
│                                              ▼                               │
│                                    ┌─────────────────┐                       │
│                                    │ Requires Human  │                       │
│                                    │    Approval     │                       │
│                                    │ [Approve/Reject]│                       │
│                                    └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Plan Execution Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   User   │     │ Frontend │     │ Planning │     │ Approval │     │   Tool   │
│          │     │          │     │   API    │     │ Service  │     │ Executor │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Click "Approve Plan"         │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2. POST /planning/{id}/execute  │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                ├────────────────┼────────────────┼────────────────┤
     │                │         STEP-BY-STEP EXECUTION                   │
     │                ├────────────────┼────────────────┼────────────────┤
     │                │                │                │                │
     │                │ 3. Execute Step 1               │                │
     │                │                │                │───────────────>│
     │                │                │                │                │
     │                │ 4. Update status: COMPLETED     │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 5. Real-time   │                │                │                │
     │    update      │                │                │                │
     │<───────────────│                │                │                │
     │                │                │                │                │
     │                │ 6. Execute Step 2               │                │
     │                │                │                │───────────────>│
     │                │                │                │                │
     │                │ 7. Step 3 requires approval     │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 8. Create ApprovalRequest       │
     │                │                │<───────────────│                │
     │                │                │                │                │
     │                │ 9. PAUSE - Wait for approval    │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 10. Show       │                │                │                │
     │    approval    │                │                │                │
     │    modal       │                │                │                │
     │<───────────────│                │                │                │
     │                │                │                │                │
     │ 11. Click Approve               │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 12. POST /approvals/{id}/approve│                │
     │                │───────────────────────────────>│                │
     │                │                │                │                │
     │                │ 13. Resume execution            │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 14. Show final result           │                │                │
     │<───────────────│                │                │                │
```

### Approval Request States

```
                          ┌─────────────┐
                          │   PENDING   │
                          └──────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
           ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
           │  APPROVED   │ │  REJECTED   │ │   EXPIRED   │
           └─────────────┘ └─────────────┘ └─────────────┘
                 │               │               │
                 ▼               ▼               ▼
           ┌───────────┐   ┌───────────┐   ┌───────────┐
           │  Execute  │   │   Stop    │   │  Cleanup  │
           │   Tool    │   │ Execution │   │  Request  │
           └───────────┘   └───────────┘   └───────────┘
```

---

## 5. Meeting Delegation Flow

### Meeting Detection & Classification

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        MEETING DELEGATION SYSTEM                              │
│                                                                               │
│  ┌─────────────┐                                                              │
│  │   CRON JOB  │ ◄─────── Runs every 5 minutes                               │
│  │ (Scheduler) │                                                              │
│  └──────┬──────┘                                                              │
│         │                                                                     │
│         ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                     MEETING DETECTION                                │     │
│  │   ┌─────────────┐                                                    │     │
│  │   │   Nylas     │ ◄─── Fetch upcoming meetings (next 24 hours)      │     │
│  │   │  Calendar   │                                                    │     │
│  │   └──────┬──────┘                                                    │     │
│  │          │                                                           │     │
│  │          ▼                                                           │     │
│  │   ┌─────────────────────────────────────────────────────────────┐   │     │
│  │   │              IMPORTANCE CLASSIFICATION                       │   │     │
│  │   │                                                              │   │     │
│  │   │   Score = 0                                                  │   │     │
│  │   │   IF VIP attendee (CEO, CTO, etc.)    → +3                  │   │     │
│  │   │   IF "urgent", "crisis" in title      → +3                  │   │     │
│  │   │   IF "decision", "review" in title    → +2                  │   │     │
│  │   │   IF >10 attendees                    → +2                  │   │     │
│  │   │   IF >5 attendees                     → +1                  │   │     │
│  │   │                                                              │   │     │
│  │   │   Score >= 5  →  CRITICAL                                    │   │     │
│  │   │   Score >= 3  →  HIGH                                        │   │     │
│  │   │   Score >= 1  →  MEDIUM                                      │   │     │
│  │   │   Score < 1   →  LOW                                         │   │     │
│  │   └─────────────────────────────────────────────────────────────┘   │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
│         │                                                                     │
│         ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                      AUTO-APPROVAL LOGIC                             │     │
│  │                                                                      │     │
│  │   CRITICAL/HIGH  →  Requires User Approval                          │     │
│  │   MEDIUM/LOW     →  Auto-Approved (Configurable)                    │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Delegation Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DELEGATION STATUS FLOW                                  │
│                                                                              │
│                           ┌──────────┐                                       │
│                           │ PENDING  │                                       │
│                           └────┬─────┘                                       │
│                                │                                             │
│                    ┌───────────┴───────────┐                                │
│                    │                       │                                 │
│              User Approves           User Rejects                           │
│                    │                       │                                 │
│                    ▼                       ▼                                 │
│              ┌──────────┐            ┌──────────┐                           │
│              │ APPROVED │            │ REJECTED │                           │
│              └────┬─────┘            └──────────┘                           │
│                   │                                                          │
│                   │ 5 min before meeting                                     │
│                   ▼                                                          │
│              ┌──────────┐                                                    │
│              │ JOINING  │ ───► AI joins via Nylas Notetaker                 │
│              └────┬─────┘                                                    │
│                   │                                                          │
│                   │ Successfully joined                                      │
│                   ▼                                                          │
│              ┌──────────┐                                                    │
│              │  JOINED  │                                                    │
│              └────┬─────┘                                                    │
│                   │                                                          │
│                   │ Meeting starts                                           │
│                   ▼                                                          │
│              ┌──────────┐                                                    │
│              │RECORDING │ ───► Transcript being captured                    │
│              └────┬─────┘                                                    │
│                   │                                                          │
│                   │ Meeting ends                                             │
│                   ▼                                                          │
│              ┌───────────────────────────────────────────────────┐          │
│              │              POST-MEETING PROCESSING               │          │
│              │                                                    │          │
│              │  1. Retrieve transcript from Nylas                 │          │
│              │  2. Analyze with LLM                               │          │
│              │  3. Generate summary                               │          │
│              │  4. Extract action items                           │          │
│              │  5. Identify decisions made                        │          │
│              │  6. Create delegation report                       │          │
│              │  7. Email report to user                           │          │
│              └───────────────────────────────────────────────────┘          │
│                   │                                                          │
│                   ▼                                                          │
│              ┌──────────┐                                                    │
│              │COMPLETED │                                                    │
│              └──────────┘                                                    │
│                                                                              │
│              ┌──────────┐                                                    │
│              │  FAILED  │ ◄── If any step fails                             │
│              └──────────┘                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AI Meeting Join Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│Scheduler │     │Delegation│     │ Notetaker│     │  Nylas   │     │   LLM    │
│          │     │ Service  │     │ Service  │     │   API    │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Check upcoming meetings      │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2. Find approved delegation     │                │
     │                │   starting in 5 min            │                │
     │                │────────────────│                │                │
     │                │                │                │                │
     │                │ 3. Request notetaker join       │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 4. POST /notetaker               │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 5. Notetaker joins meeting       │
     │                │                │<───────────────│                │
     │                │                │                │                │
     │                │ 6. Update status: JOINED        │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │                │                │    (Meeting in progress)        │
     │                │                │                │                │
     │                │                │ 7. GET /notetaker/{id}/transcript
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │ 8. Return transcript            │
     │                │                │<───────────────│                │
     │                │                │                │                │
     │                │ 9. Analyze transcript           │                │
     │                │────────────────────────────────────────────────>│
     │                │                │                │                │
     │                │ 10. Generate report             │                │
     │                │<────────────────────────────────────────────────│
     │                │                │                │                │
     │                │ 11. Save report, extract action items            │
     │                │────────────────│                │                │
     │                │                │                │                │
     │                │ 12. Email report to user        │                │
     │                │────────────────│                │                │
```

---

## 6. AI Interview Flow

### Complete Interview Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI INTERVIEW LIFECYCLE                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      1. SCHEDULING PHASE                             │    │
│  │                                                                      │    │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │    │
│  │   │ Enter    │───>│  Select  │───>│ Schedule │───>│ Create   │     │    │
│  │   │ Candidate│    │Interview │    │   Time   │    │ Session  │     │    │
│  │   │  Info    │    │   Type   │    │          │    │          │     │    │
│  │   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │    │
│  │                                                                      │    │
│  │   Status: SCHEDULED                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    2. PREPARATION PHASE                              │    │
│  │                                                                      │    │
│  │   ┌──────────────────────────────────────────────────────────────┐  │    │
│  │   │                 QUESTION GENERATION                           │  │    │
│  │   │                                                               │  │    │
│  │   │   INPUT:                                                      │  │    │
│  │   │   - Position: Senior Software Engineer                        │  │    │
│  │   │   - Type: Technical Interview                                 │  │    │
│  │   │   - Skills: Python, FastAPI, PostgreSQL                       │  │    │
│  │   │                                                               │  │    │
│  │   │   ┌─────────┐         ┌─────────────────────────────────┐    │  │    │
│  │   │   │   LLM   │ ──────► │  8-10 Tailored Questions        │    │  │    │
│  │   │   └─────────┘         │  - Competency-based             │    │  │    │
│  │   │                       │  - Difficulty-weighted          │    │  │    │
│  │   │                       │  - With expected answer points  │    │  │    │
│  │   │                       └─────────────────────────────────┘    │  │    │
│  │   └──────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  │   ┌──────────────────────────────────────────────────────────────┐  │    │
│  │   │               TTS AUDIO GENERATION                            │  │    │
│  │   │                                                               │  │    │
│  │   │   Question Text ──► gTTS/ElevenLabs ──► MP3 Audio Files      │  │    │
│  │   │                                                               │  │    │
│  │   │   "Hello, I'm your AI interviewer. Let's begin..."           │  │    │
│  │   │   "Question 1: Tell me about your experience with..."        │  │    │
│  │   └──────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  │   Status: READY                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      3. INTERVIEW PHASE                              │    │
│  │                                                                      │    │
│  │   ┌───────────────────────────────────────────────────────────┐     │    │
│  │   │                    MEETING ROOM                            │     │    │
│  │   │                                                            │     │    │
│  │   │   ┌─────────────┐              ┌─────────────┐            │     │    │
│  │   │   │  Candidate  │              │ AI Notetaker│            │     │    │
│  │   │   │   (Human)   │              │  (Recording)│            │     │    │
│  │   │   └─────────────┘              └─────────────┘            │     │    │
│  │   │                                                            │     │    │
│  │   │   AI speaks via TTS:                                       │     │    │
│  │   │   🎤 "Question 1: Can you walk me through..."             │     │    │
│  │   │                                                            │     │    │
│  │   │   Candidate responds:                                      │     │    │
│  │   │   🗣️ "In my previous role at XYZ..."                      │     │    │
│  │   │                                                            │     │    │
│  │   │   📝 Transcript being captured in real-time               │     │    │
│  │   └───────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │   Status: IN_PROGRESS                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     4. ANALYSIS PHASE                                │    │
│  │                                                                      │    │
│  │   Status: ANALYZING                                                  │    │
│  │                                                                      │    │
│  │   ┌───────────────────────────────────────────────────────────┐     │    │
│  │   │              TRANSCRIPT ANALYSIS (LLM)                     │     │    │
│  │   │                                                            │     │    │
│  │   │   For each question:                                       │     │    │
│  │   │   1. Extract candidate's answer from transcript           │     │    │
│  │   │   2. Compare against expected keywords/points             │     │    │
│  │   │   3. Score answer (0-10)                                  │     │    │
│  │   │   4. Generate detailed feedback                           │     │    │
│  │   │                                                            │     │    │
│  │   │   ┌─────────────────────────────────────────────────────┐ │     │    │
│  │   │   │ Q1: Tell me about your Python experience            │ │     │    │
│  │   │   │ Answer: "I've used Python for 5 years..."           │ │     │    │
│  │   │   │ Score: 8/10                                          │ │     │    │
│  │   │   │ Feedback: Strong practical experience shown...       │ │     │    │
│  │   │   └─────────────────────────────────────────────────────┘ │     │    │
│  │   └───────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  │   ┌───────────────────────────────────────────────────────────┐     │    │
│  │   │                  SCORING ALGORITHM                         │     │    │
│  │   │                                                            │     │    │
│  │   │   Overall Score = Σ(answer_score × question_weight)       │     │    │
│  │   │                  ─────────────────────────────────         │     │    │
│  │   │                       Σ(question_weight) × 10              │     │    │
│  │   │                                                            │     │    │
│  │   │   RECOMMENDATION:                                          │     │    │
│  │   │   Score >= 85  →  STRONG_HIRE                             │     │    │
│  │   │   Score >= 70  →  HIRE                                    │     │    │
│  │   │   Score >= 55  →  MAYBE                                   │     │    │
│  │   │   Score >= 40  →  NO_HIRE                                 │     │    │
│  │   │   Score < 40   →  STRONG_NO_HIRE                          │     │    │
│  │   └───────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      5. REPORT PHASE                                 │    │
│  │                                                                      │    │
│  │   Status: COMPLETED                                                  │    │
│  │                                                                      │    │
│  │   ┌────────────────────────────────────────────────────────────┐    │    │
│  │   │              INTERVIEW EVALUATION REPORT                    │    │    │
│  │   │                                                             │    │    │
│  │   │   Candidate: John Doe                                       │    │    │
│  │   │   Position: Senior Software Engineer                        │    │    │
│  │   │   Date: August 20, 2026                                     │    │    │
│  │   │                                                             │    │    │
│  │   │   ┌───────────────────────────────────────────────────┐    │    │    │
│  │   │   │  OVERALL SCORE: 82%      RECOMMENDATION: HIRE     │    │    │    │
│  │   │   └───────────────────────────────────────────────────┘    │    │    │
│  │   │                                                             │    │    │
│  │   │   COMPETENCY BREAKDOWN:                                     │    │    │
│  │   │   ████████░░ Problem Solving: 8/10                         │    │    │
│  │   │   ███████░░░ Technical: 7/10                               │    │    │
│  │   │   █████████░ Communication: 9/10                           │    │    │
│  │   │   ███████░░░ System Design: 7/10                           │    │    │
│  │   │                                                             │    │    │
│  │   │   STRENGTHS:                                                │    │    │
│  │   │   ✓ Strong practical Python experience                     │    │    │
│  │   │   ✓ Excellent communication skills                         │    │    │
│  │   │   ✓ Good problem-solving approach                          │    │    │
│  │   │                                                             │    │    │
│  │   │   AREAS FOR IMPROVEMENT:                                    │    │    │
│  │   │   ⚠ Could deepen system design knowledge                   │    │    │
│  │   │   ⚠ More experience with distributed systems               │    │    │
│  │   └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │   [View Full Report] [Send to Hiring Manager] [Download PDF]         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Interview Status Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌───────────┐     ┌──────────┐
│SCHEDULED │────>│PREPARING │────>│  READY   │────>│IN_PROGRESS│────>│ANALYZING │
└──────────┘     └──────────┘     └──────────┘     └───────────┘     └──────────┘
     │                │                │                 │                │
     │                │                │                 │                │
     ▼                ▼                ▼                 ▼                ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│CANCELLED │     │  FAILED  │     │  FAILED  │     │  FAILED  │     │COMPLETED │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
```

---

## 7. Data Flow Diagrams

### Overall System Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM DATA FLOW                                    │
│                                                                              │
│   ┌─────────────┐                          ┌─────────────────────────────┐  │
│   │    USER     │                          │       EXTERNAL SERVICES      │  │
│   │  (Browser)  │                          │                              │  │
│   └──────┬──────┘                          │  ┌─────────┐ ┌─────────────┐│  │
│          │                                  │  │  Nylas  │ │ Groq LLM   ││  │
│          │ HTTP/REST                        │  │Calendar │ │            ││  │
│          │                                  │  │ Email   │ │            ││  │
│          ▼                                  │  │Notetaker│ │            ││  │
│   ┌──────────────┐                          │  └────┬────┘ └──────┬─────┘│  │
│   │   FRONTEND   │                          │       │             │      │  │
│   │   (React)    │                          └───────┼─────────────┼──────┘  │
│   │              │                                  │             │         │
│   │ ┌──────────┐ │                                  │             │         │
│   │ │  Zustand │ │                                  │             │         │
│   │ │  Store   │ │                                  │             │         │
│   │ └──────────┘ │                                  │             │         │
│   └──────┬───────┘                                  │             │         │
│          │                                          │             │         │
│          │ API Calls                                │             │         │
│          │                                          │             │         │
│          ▼                                          │             │         │
│   ┌─────────────────────────────────────────────────┼─────────────┼──────┐  │
│   │                    BACKEND (FastAPI)            │             │      │  │
│   │                                                 │             │      │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │             │      │  │
│   │  │  Auth    │  │  Agent   │  │Delegation│ <────┘             │      │  │
│   │  │ Service  │  │ Executor │  │ Service  │                    │      │  │
│   │  └────┬─────┘  └────┬─────┘  └────┬─────┘                    │      │  │
│   │       │             │             │                          │      │  │
│   │       │             │             │      ┌──────────┐        │      │  │
│   │       │             │             │      │Interview │ <──────┘      │  │
│   │       │             │             │      │ Service  │               │  │
│   │       │             │             │      └────┬─────┘               │  │
│   │       │             │             │           │                     │  │
│   │       ▼             ▼             ▼           ▼                     │  │
│   │  ┌─────────────────────────────────────────────────────────────┐   │  │
│   │  │                    REPOSITORY LAYER                          │   │  │
│   │  │    (BaseRepository, ScopedRepository, UnitOfWork)            │   │  │
│   │  └──────────────────────────────┬──────────────────────────────┘   │  │
│   └─────────────────────────────────┼──────────────────────────────────┘  │
│                                     │                                      │
│                                     │ SQLAlchemy ORM                       │
│                                     │                                      │
│                                     ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                        DATABASE LAYER                                │ │
│   │                                                                      │ │
│   │  ┌─────────────────────────────────────────────────────────────┐   │ │
│   │  │                    PostgreSQL (AI_Workforce)                 │   │ │
│   │  │                                                              │   │ │
│   │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐               │   │ │
│   │  │  │   users    │ │   agents   │ │conversations│               │   │ │
│   │  │  └────────────┘ └────────────┘ └────────────┘               │   │ │
│   │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐               │   │ │
│   │  │  │  messages  │ │delegations │ │ interviews │               │   │ │
│   │  │  └────────────┘ └────────────┘ └────────────┘               │   │ │
│   │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐               │   │ │
│   │  │  │ approvals  │ │   plans    │ │ questions  │               │   │ │
│   │  │  └────────────┘ └────────────┘ └────────────┘               │   │ │
│   │  └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │  ┌─────────────────────────────────────────────────────────────┐   │ │
│   │  │                     Redis (Cache)                            │   │ │
│   │  │  - Session tokens                                            │   │ │
│   │  │  - Rate limiting counters                                    │   │ │
│   │  │  - Temporary state                                           │   │ │
│   │  └─────────────────────────────────────────────────────────────┘   │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE ENTITY RELATIONSHIPS                        │
│                                                                              │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐         │
│  │ Organization │ 1───────M│    User      │ 1───────M│    Agent     │         │
│  │              │         │              │         │              │         │
│  │ id           │         │ id           │         │ id           │         │
│  │ name         │         │ email        │         │ name         │         │
│  │ plan_type    │         │ password_hash│         │ description  │         │
│  └──────────────┘         │ name         │         │ instructions │         │
│         │                 │ role         │         └───────┬──────┘         │
│         │                 │ org_id (FK)  │                 │                │
│         │                 └──────────────┘                 │                │
│         │                        │                         │                │
│         │                        │                         │                │
│         │                        │                    1────┴────M           │
│         │                        │                         │                │
│         │                        │                 ┌───────┴──────┐         │
│         │                        │                 │Conversation  │         │
│         │                        │                 │              │         │
│         │                        │ 1───────M       │ id           │         │
│         │                        │                 │ user_id (FK) │         │
│         │                        │                 │ agent_id (FK)│         │
│         │                        │                 │ title        │         │
│         │                        │                 └───────┬──────┘         │
│         │                        │                         │                │
│         │                        │                    1────┴────M           │
│         │                        │                         │                │
│         │                        │                 ┌───────┴──────┐         │
│         │                        │                 │   Message    │         │
│         │                        │                 │              │         │
│         │                        │                 │ id           │         │
│         │                        │                 │ conv_id (FK) │         │
│         │                        │                 │ role         │         │
│         │                        │                 │ content      │         │
│         │                        │                 └──────────────┘         │
│         │                        │                                          │
│    1────┴────M              1────┴────M                                     │
│         │                        │                                          │
│ ┌───────┴───────┐        ┌───────┴───────┐        ┌──────────────┐         │
│ │MeetingDelegation│       │InterviewSession│ 1─────M│InterviewQuestion│       │
│ │               │        │               │        │              │         │
│ │ id            │        │ id            │        │ id           │         │
│ │ user_id (FK)  │        │ user_id (FK)  │        │ interview_id │         │
│ │ org_id (FK)   │        │ org_id (FK)   │        │ question_text│         │
│ │ meeting_id    │        │ candidate_name│        │ score        │         │
│ │ meeting_title │        │ position_title│        │ answer       │         │
│ │ importance    │        │ interview_type│        │ feedback     │         │
│ │ status        │        │ overall_score │        └──────────────┘         │
│ │ transcript    │        │recommendation │                                  │
│ │ report        │        └───────────────┘                                  │
│ └───────────────┘                                                           │
│                                                                              │
│  ┌──────────────┐         ┌──────────────┐                                  │
│  │ExecutionPlan │ 1───────M│ApprovalRequest│                                 │
│  │              │         │              │                                  │
│  │ id           │         │ id           │                                  │
│  │ conv_id (FK) │         │ plan_id (FK) │                                  │
│  │ user_request │         │ tool_name    │                                  │
│  │ plan_data    │         │ status       │                                  │
│  │ status       │         │ expires_at   │                                  │
│  └──────────────┘         └──────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. API Integration Flow

### Nylas Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NYLAS INTEGRATION                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     CALENDAR OPERATIONS                              │    │
│  │                                                                      │    │
│  │   GET /calendars          - List user calendars                     │    │
│  │   GET /events             - List calendar events                    │    │
│  │   POST /events            - Create calendar event                   │    │
│  │   PUT /events/{id}        - Update calendar event                   │    │
│  │   DELETE /events/{id}     - Delete calendar event                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      EMAIL OPERATIONS                                │    │
│  │                                                                      │    │
│  │   GET /messages           - List email messages                     │    │
│  │   GET /messages/{id}      - Get specific email                      │    │
│  │   POST /messages          - Send email                              │    │
│  │   POST /drafts            - Create email draft                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    NOTETAKER OPERATIONS                              │    │
│  │                                                                      │    │
│  │   POST /notetaker         - Join meeting                            │    │
│  │   GET /notetaker/{id}     - Get notetaker status                    │    │
│  │   GET /notetaker/{id}/transcript - Get meeting transcript           │    │
│  │   DELETE /notetaker/{id}  - Leave meeting                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Groq LLM Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GROQ LLM INTEGRATION                                │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                        REQUEST FORMAT                                 │  │
│   │                                                                       │  │
│   │   {                                                                   │  │
│   │     "model": "llama-3.3-70b-versatile",                              │  │
│   │     "messages": [                                                     │  │
│   │       {"role": "system", "content": "You are..."},                   │  │
│   │       {"role": "user", "content": "User message"}                    │  │
│   │     ],                                                                │  │
│   │     "tools": [...],  // Optional: function calling                   │  │
│   │     "temperature": 0.7                                                │  │
│   │   }                                                                   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│   USE CASES:                                                                 │
│   ┌────────────────────────────────────────────────────────────┐            │
│   │ 1. Chat Conversations                                       │            │
│   │    - Agent responses to user messages                       │            │
│   │    - Context-aware dialogue                                 │            │
│   └────────────────────────────────────────────────────────────┘            │
│   ┌────────────────────────────────────────────────────────────┐            │
│   │ 2. Planning                                                 │            │
│   │    - Analyze user requests                                  │            │
│   │    - Generate multi-step plans                              │            │
│   └────────────────────────────────────────────────────────────┘            │
│   ┌────────────────────────────────────────────────────────────┐            │
│   │ 3. Meeting Analysis                                         │            │
│   │    - Summarize transcripts                                  │            │
│   │    - Extract action items                                   │            │
│   └────────────────────────────────────────────────────────────┘            │
│   ┌────────────────────────────────────────────────────────────┐            │
│   │ 4. Interview Analysis                                       │            │
│   │    - Generate questions                                     │            │
│   │    - Score candidate answers                                │            │
│   │    - Generate evaluation reports                            │            │
│   └────────────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete API Endpoint Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API ENDPOINT MAP                                  │
│                                                                              │
│  BASE URL: http://localhost:8000/api/v1                                     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ AUTHENTICATION                                                          │ │
│  │ POST   /auth/register        Register new user                         │ │
│  │ POST   /auth/login           Login user                                │ │
│  │ GET    /auth/me              Get current user                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ AGENTS                                                                  │ │
│  │ GET    /agents               List all agents                           │ │
│  │ POST   /agents               Create new agent                          │ │
│  │ GET    /agents/{id}          Get agent details                         │ │
│  │ PUT    /agents/{id}          Update agent                              │ │
│  │ DELETE /agents/{id}          Delete agent                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ CONVERSATIONS                                                           │ │
│  │ GET    /conversations              List conversations                  │ │
│  │ POST   /conversations              Create conversation                 │ │
│  │ GET    /conversations/{id}         Get conversation                    │ │
│  │ DELETE /conversations/{id}         Delete conversation                 │ │
│  │ GET    /conversations/{id}/messages     Get messages                   │ │
│  │ POST   /conversations/{id}/messages     Send message                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ PLANNING                                                                │ │
│  │ POST   /planning                   Create execution plan               │ │
│  │ GET    /planning/{id}              Get plan status                     │ │
│  │ POST   /planning/{id}/execute      Execute plan                        │ │
│  │ POST   /planning/{id}/cancel       Cancel plan                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ APPROVALS                                                               │ │
│  │ GET    /approvals                  List pending approvals              │ │
│  │ GET    /approvals/{id}             Get approval details                │ │
│  │ POST   /approvals/{id}/approve     Approve request                     │ │
│  │ POST   /approvals/{id}/reject      Reject request                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ DELEGATIONS                                                             │ │
│  │ GET    /delegations                List all delegations                │ │
│  │ GET    /delegations/stats          Get delegation statistics           │ │
│  │ GET    /delegations/pending        Get pending delegations             │ │
│  │ GET    /delegations/upcoming       Get upcoming delegations            │ │
│  │ GET    /delegations/{id}           Get delegation details              │ │
│  │ GET    /delegations/{id}/report    Get delegation report               │ │
│  │ POST   /delegations/{id}/approve   Approve delegation                  │ │
│  │ POST   /delegations/{id}/reject    Reject delegation                   │ │
│  │ POST   /delegations/{id}/join      AI joins meeting                    │ │
│  │ POST   /delegations/process-meetings  Scan calendar                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ INTERVIEWS                                                              │ │
│  │ GET    /interviews                 List all interviews                 │ │
│  │ GET    /interviews/stats           Get interview statistics            │ │
│  │ GET    /interviews/upcoming        Get upcoming interviews             │ │
│  │ POST   /interviews                 Schedule new interview              │ │
│  │ GET    /interviews/{id}            Get interview details               │ │
│  │ PUT    /interviews/{id}            Update interview                    │ │
│  │ DELETE /interviews/{id}            Cancel interview                    │ │
│  │ POST   /interviews/{id}/generate-questions  Generate questions         │ │
│  │ GET    /interviews/{id}/questions  Get all questions                   │ │
│  │ POST   /interviews/{id}/start      Start interview                     │ │
│  │ POST   /interviews/{id}/end        End & analyze interview             │ │
│  │ GET    /interviews/{id}/report     Get evaluation report               │ │
│  │ POST   /interviews/{id}/generate-audio  Generate TTS audio             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

The AI Workforce Platform provides a comprehensive workflow for:

1. **User Management**: Secure JWT-based authentication with role-based access control
2. **Multi-Agent System**: Create and manage specialized AI agents with custom tool permissions
3. **Intelligent Planning**: LangGraph-powered multi-step execution with human approval gates
4. **Meeting Delegation**: Automated meeting attendance with AI-generated reports
5. **AI Interviews**: End-to-end automated interviews with TTS speaking capability and scoring

Each component is designed to work seamlessly together while maintaining clear separation of concerns through the layered architecture (Frontend → API → Services → Repositories → Database).
