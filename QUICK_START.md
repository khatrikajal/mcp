# Quick Start Guide - AI Workforce Platform

## 🚀 Start the Full Stack Application

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ installed
- All dependencies installed (see setup below)

---

## Step 1: Install Dependencies

### Backend (if not already installed)
```bash
pip install -r requirements.txt
```

### Frontend (if not already installed)
```bash
cd client/frontend
npm install
cd ../..
```

---

## Step 2: Start the Servers

You need 2 terminals (3 if you want MCP tools):

### Terminal 1: Start Backend API
```bash
python start_api.py
```

You should see:
```
Starting AI Workforce Platform API on 0.0.0.0:8001
API documentation: http://0.0.0.0:8001/docs

Default login credentials:
  Email: admin@example.com
  Password: admin123
```

**API will run on:** http://localhost:8001

### Terminal 2: Start Frontend
```bash
cd client/frontend
npm run dev
```

You should see:
```
VITE v8.2.1  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**Frontend will run on:** http://localhost:5173

### Terminal 3 (Optional): Start MCP Server for Tools
```bash
python -m server.app
```

**MCP Server will run on:** http://localhost:8000

---

## Step 3: Test the Application

### 3.1 Open Frontend
1. Open browser: http://localhost:5173
2. You should see the **Login Page**

### 3.2 Login
Use the default admin credentials:
- **Email:** admin@example.com
- **Password:** admin123

Click "Login"

### 3.3 Success!
You should be redirected to the **Dashboard** showing:
- Your user info (Admin User)
- Organization cards
- Agent management section
- Various platform features

---

## 🎯 What You Can Do Now

### 1. View Your Agent
The default "General Assistant" agent has been created with all MCP tools enabled.

### 2. Create a New User
1. Logout (top right)
2. Click "Register"
3. Create a new account
4. Login with new credentials
5. You'll have your own organization and can create agents

### 3. Explore API Documentation
Visit: http://localhost:8001/docs

Interactive Swagger UI to test all API endpoints.

### 4. Create a New Agent (Coming in Phase 2)
Agent builder UI will allow:
- Custom name and description
- System instructions
- Tool permission configuration

---

## 📊 Architecture Running

```
Frontend (React)          → http://localhost:5173
    ↓
Backend API (FastAPI)     → http://localhost:8001
    ↓
Database (SQLite)         → mcp_platform.db

MCP Server (optional)     → http://localhost:8000
```

---

## 🐛 Common Issues

### Issue: Port already in use
**Solution:**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8001
kill -9 <PID>
```

### Issue: Login button does nothing
**Checklist:**
1. ✅ Backend API running on port 8001?
2. ✅ Frontend running on port 5173?
3. ✅ Check browser console for errors (F12)
4. ✅ Verify credentials: admin@example.com / admin123

### Issue: CORS errors in browser
**Solution:**
- Make sure BOTH servers are running
- Check frontend .env: `VITE_API_BASE_URL=http://localhost:8001`
- Clear browser cache (Ctrl+Shift+Delete)

### Issue: "Email already registered"
**Solution:**
- This email is already in the database
- Either login with existing credentials
- Or use a different email to register

---

## 🔄 Restart from Scratch

If you want to reset everything:

```bash
# Stop all servers (Ctrl+C in each terminal)

# Delete database
rm mcp_platform.db

# Re-seed database
python -m server.api.seed

# Restart servers
python start_api.py
# (in new terminal) cd client/frontend && npm run dev
```

---

## 📝 Test Credentials

**Admin User:**
- Email: admin@example.com
- Password: admin123
- Role: admin
- Organization: Default Organization

**Test New Registration:**
- Create any email (test@example.com)
- Password: minimum 8 characters
- Creates new organization automatically

---

## ✅ Verification Checklist

After starting both servers, verify:

- [ ] Backend API responds: http://localhost:8001/health
- [ ] Frontend loads: http://localhost:5173
- [ ] Login page visible
- [ ] Can login with admin@example.com / admin123
- [ ] Dashboard shows user info
- [ ] Browser console has no errors (F12)
- [ ] Can logout and login again

---

## 🎉 Next Steps

### Phase 2 - Multi-Agent Chat
- [ ] Build chat interface
- [ ] Connect to MCP tools
- [ ] Conversation history
- [ ] Agent selector

### Phase 3 - Planning Workflows
- [ ] LangGraph integration
- [ ] Plan visualization
- [ ] Approval gates

### Phase 4 - Meeting Delegation
- [ ] Auto-join meetings
- [ ] Importance classification
- [ ] Meeting reports

---

## 📚 Documentation

- **Complete Setup:** [BACKEND_INTEGRATION_COMPLETE.md](BACKEND_INTEGRATION_COMPLETE.md)
- **Frontend Guide:** [client/frontend/README.md](client/frontend/README.md)
- **Notetaker Flow:** [NYLAS_NOTETAKER_FLOW.md](NYLAS_NOTETAKER_FLOW.md)
- **Implementation Plan:** [~/.claude/plans/serene-marinating-book.md]

---

**Ready to build the AI Workforce Platform!** 🚀
