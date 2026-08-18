# AI Workforce Platform - Frontend

Modern React + TypeScript frontend for the AI Workforce Platform with authentication, multi-agent workspace, and real-time features.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router v6** - Client-side routing
- **Zustand** - State management with persistence
- **Axios** - HTTP client with JWT interceptors
- **Tailwind CSS** - Utility-first CSS framework
- **ShadCN UI** - Accessible component patterns

## Project Structure

```
src/
├── components/
│   ├── agents/           # Agent management components
│   ├── chat/             # Chat interface components
│   ├── planning/         # Planning workflow visualization
│   ├── approvals/        # Approval center components
│   ├── delegations/      # Meeting delegation dashboard
│   ├── interviews/       # Interview automation UI
│   ├── ui/               # Base UI components (Button, Input, Card, etc.)
│   └── ProtectedRoute.tsx  # Auth guard for routes
├── pages/
│   ├── LoginPage.tsx     # Login form
│   ├── RegisterPage.tsx  # Registration form
│   └── DashboardPage.tsx # Main dashboard
├── services/
│   └── api.ts            # API client with JWT auth
├── stores/
│   └── authStore.ts      # Zustand auth state management
├── types/
│   └── index.ts          # TypeScript type definitions
├── lib/
│   └── utils.ts          # Utility functions
└── hooks/                # Custom React hooks
```

## Features

### Authentication
- JWT-based authentication
- Persistent login state (localStorage)
- Auto-redirect on token expiration
- Protected routes with auth guards
- Login and registration forms with validation

### Routing
- Public routes: `/login`, `/register`
- Protected routes: `/` (dashboard)
- Auto-redirect authenticated users from public routes
- 404 handling with smart redirects

### API Integration
- Axios client with request/response interceptors
- Automatic JWT token injection in headers
- Error handling with 401 auto-logout
- TypeScript-first API methods

### State Management
- Zustand store for global auth state
- Persistent state across page refreshes
- Optimistic UI updates
- Error state management

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Running backend API on `http://localhost:8001`

### Installation

```bash
cd client/frontend
npm install
```

### Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8001
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

The optimized build will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## API Endpoints Used

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user

### Agents (Coming Soon)
- `GET /api/v1/agents` - List all agents
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents/:id` - Get agent details
- `PUT /api/v1/agents/:id` - Update agent
- `DELETE /api/v1/agents/:id` - Delete agent

### Conversations (Coming Soon)
- `GET /api/v1/conversations` - List conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/:id/messages` - Get messages
- `POST /api/v1/conversations/:id/messages` - Send message

## Component Library

### UI Components

All UI components follow ShadCN patterns with Tailwind CSS:

- **Button** - Multiple variants (default, outline, destructive, etc.)
- **Input** - Form input with focus states
- **Label** - Accessible form labels
- **Card** - Content containers with header/footer

### Custom Components

- **ProtectedRoute** - Auth guard wrapper for protected pages
- **LoginPage** - Full login form with validation
- **RegisterPage** - Registration form with password confirmation
- **DashboardPage** - Main application dashboard

## Authentication Flow

1. User visits `/` → Redirected to `/login` (if not authenticated)
2. User enters credentials → API call to `/api/v1/auth/login`
3. Backend returns JWT token + user data
4. Token stored in `localStorage`, user data in Zustand store
5. User redirected to `/` (dashboard)
6. All subsequent API calls include JWT in `Authorization` header
7. On 401 error → Token cleared, redirect to `/login`

## Styling

This project uses Tailwind CSS with a custom color palette defined in CSS variables:

- Light/dark mode support
- Semantic color tokens (primary, secondary, destructive, etc.)
- Responsive utilities
- Custom spacing and border radius

## Type Safety

Full TypeScript coverage with:

- API request/response types
- Component prop types
- Store state types
- Route parameter types

## Next Steps

### Phase 2 Remaining Tasks:
- [ ] Add TanStack Query for server state management
- [ ] Create agent management components
- [ ] Build chat interface
- [ ] Add conversation history
- [ ] Implement real-time message streaming (optional)

### Phase 3+:
- [ ] Planning workflow visualization (ReactFlow)
- [ ] Approval center
- [ ] Meeting delegation dashboard
- [ ] Interview automation UI

## Development Guidelines

### Code Style
- Use functional components with hooks
- Prefer TypeScript interfaces over types
- Use arrow functions for components
- Extract reusable logic to custom hooks

### File Naming
- Components: PascalCase (e.g., `DashboardPage.tsx`)
- Utilities: camelCase (e.g., `utils.ts`)
- Stores: camelCase with "Store" suffix (e.g., `authStore.ts`)

### Component Structure
```tsx
// Imports
import { useState } from "react";
import { useAuthStore } from "../stores/authStore";

// Types
interface Props {
  title: string;
}

// Component
export function MyComponent({ title }: Props) {
  // Hooks
  const { user } = useAuthStore();
  const [state, setState] = useState();

  // Handlers
  const handleClick = () => {};

  // Render
  return <div>{title}</div>;
}
```

## Troubleshooting

### Common Issues

**Issue: API calls fail with CORS error**
- Ensure backend is running on `http://localhost:8001`
- Check that CORS is configured in the FastAPI backend

**Issue: Login succeeds but page doesn't redirect**
- Check browser console for errors
- Verify JWT token is being stored in localStorage
- Check Zustand store state in React DevTools

**Issue: Styles not loading**
- Run `npm install` to ensure Tailwind is installed
- Check that `index.css` imports Tailwind directives
- Verify `tailwind.config.js` has correct content paths

## Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vite.dev/)
- [React Router](https://reactrouter.com/)
- [Zustand](https://github.com/pmndrs/zustand)
- [Tailwind CSS](https://tailwindcss.com/)
- [ShadCN UI](https://ui.shadcn.com/)
