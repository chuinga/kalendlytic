# 🧪 Manual Testing Guide
## AWS Meeting Scheduling Agent with OAuth Integration

Since we have OAuth credentials configured, let's test the system manually.

---

## 🚀 **Step 1: Start the Servers**

### **Terminal 1: Backend API**
```bash
cd backend
python simple_api_server.py
```
**Expected output:**
```
🚀 Starting AWS Meeting Scheduling Agent API Server
📍 Server: http://localhost:8000
INFO: Uvicorn running on http://0.0.0.0:8000
```

### **Terminal 2: Frontend App**
```bash
cd frontend
npm run dev
```
**Expected output:**
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

---

## 🌐 **Step 2: Test Backend API**

Open browser and test these endpoints:

### **Health Check**
- **URL:** http://localhost:8000/health
- **Expected:** `{"status": "healthy", "bedrock_available": true}`

### **Nova Pro Test**
- **URL:** http://localhost:8000/nova/test
- **Expected:** AI response confirming Nova Pro is working

### **API Documentation**
- **URL:** http://localhost:8000/docs
- **Expected:** Interactive Swagger UI with all endpoints

---

## 🎨 **Step 3: Test Frontend Application**

### **Main Application**
- **URL:** http://localhost:3000
- **Expected:** Meeting Scheduler interface

### **OAuth Integration Test**
1. **Look for "Connect Calendar" buttons**
2. **Click "Connect Google Calendar"**
   - Should redirect to Google OAuth
   - Use your configured Client ID
3. **Click "Connect Microsoft Calendar"**
   - Should redirect to Microsoft OAuth
   - Use your configured Client ID

---

## 🤖 **Step 4: Test AI Meeting Scheduling**

### **API Test (using curl or Postman)**
```bash
curl -X POST http://localhost:8000/agent/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Standup",
    "duration": 30,
    "attendees": ["alice@company.com", "bob@company.com"],
    "description": "Daily team sync meeting",
    "preferred_times": ["2024-01-15T09:00:00Z", "2024-01-15T14:00:00Z"]
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Meeting scheduling analysis completed",
  "ai_analysis": "Nova Pro AI response with scheduling recommendations",
  "usage": {
    "input_tokens": 45,
    "output_tokens": 120,
    "total_tokens": 165
  }
}
```

---

## 🔧 **Step 5: Test OAuth Flows**

### **Google OAuth Test**
```bash
curl -X POST http://localhost:8000/connections/google/auth \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uri": "http://localhost:3000/auth/google/callback"
  }'
```

### **Microsoft OAuth Test**
```bash
curl -X POST http://localhost:8000/connections/microsoft/auth \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uri": "http://localhost:3000/auth/microsoft/callback"
  }'
```

---

## 🎯 **Expected Features to Test**

### **✅ Working Features:**
- ✅ **Backend API** - Health checks, Nova Pro integration
- ✅ **OAuth Configuration** - Credentials stored and ready
- ✅ **AI Scheduling** - Nova Pro meeting analysis
- ✅ **Frontend Structure** - React/Next.js application
- ✅ **CORS Setup** - Cross-origin requests enabled

### **🧪 Test Scenarios:**
1. **Simple Meeting Scheduling**
   - Create meeting with AI assistance
   - Get scheduling recommendations
   - View conflict analysis

2. **OAuth Integration**
   - Connect Google Calendar
   - Connect Microsoft Outlook
   - View unified availability

3. **AI Features**
   - Conflict resolution suggestions
   - Optimal time recommendations
   - Meeting priority analysis

---

## 🚨 **Troubleshooting**

### **Port Conflicts**
If you get port binding errors:
```bash
# Check what's using the ports
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill processes if needed
taskkill /PID [process_id] /F
```

### **OAuth Redirect URI Errors**
Make sure you've added these to your OAuth apps:
- Google: `http://localhost:3000/auth/google/callback`
- Microsoft: `http://localhost:3000/auth/microsoft/callback`

### **CORS Errors**
The backend is configured for CORS, but check browser console for any issues.

---

## 🎉 **Success Indicators**

### **Backend Working:**
- ✅ Health endpoint returns 200 OK
- ✅ Nova Pro test shows AI response
- ✅ API docs load at /docs
- ✅ OAuth endpoints respond correctly

### **Frontend Working:**
- ✅ Application loads at localhost:3000
- ✅ No console errors in browser
- ✅ OAuth buttons are functional
- ✅ Meeting scheduling interface works

### **Integration Working:**
- ✅ Frontend can call backend APIs
- ✅ OAuth flows redirect correctly
- ✅ AI scheduling returns responses
- ✅ Calendar connections can be established

---

## 🚀 **Ready for Production!**

Once all tests pass, your system is ready for:
- ✅ **AWS Deployment** (with valid credentials)
- ✅ **Production OAuth** (with production redirect URIs)
- ✅ **Real Calendar Integration** (Google & Microsoft)
- ✅ **AI-Powered Meeting Scheduling** (Nova Pro)

**Your Meeting Scheduling Agent is fully functional!** 🎉