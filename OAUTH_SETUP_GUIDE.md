# 🔐 OAuth Credentials Setup Guide
## Google Calendar & Microsoft Outlook Integration

This guide will help you set up OAuth credentials for calendar integrations.

---

## 🟦 **Google Calendar OAuth Setup**

### **Step 1: Create Google Cloud Project**

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create New Project**
   - Click "Select a project" → "New Project"
   - Project name: `meeting-scheduler-oauth`
   - Click "Create"

3. **Enable APIs**
   - Go to "APIs & Services" → "Library"
   - Search and enable:
     - **Google Calendar API**
     - **Gmail API** (for email notifications)
     - **Google+ API** (for user info)

### **Step 2: Configure OAuth Consent Screen**

1. **Go to OAuth Consent Screen**
   - Navigate: APIs & Services → OAuth consent screen
   - User Type: **External** (for public use)
   - Click "Create"

2. **Fill App Information**
   ```
   App name: Meeting Scheduler
   User support email: your-email@domain.com
   Developer contact: your-email@domain.com
   ```

3. **Add Scopes**
   - Click "Add or Remove Scopes"
   - Add these scopes:
     ```
     https://www.googleapis.com/auth/calendar
     https://www.googleapis.com/auth/calendar.events
     https://www.googleapis.com/auth/userinfo.email
     https://www.googleapis.com/auth/userinfo.profile
     ```

4. **Add Test Users** (for development)
   - Add your email and test user emails
   - Click "Save and Continue"

### **Step 3: Create OAuth Credentials**

1. **Go to Credentials**
   - Navigate: APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"

2. **Configure OAuth Client**
   ```
   Application type: Web application
   Name: Meeting Scheduler Web Client
   
   Authorized JavaScript origins:
   - http://localhost:3000 (for development)
   - https://your-domain.com (for production)
   
   Authorized redirect URIs:
   - http://localhost:3000/auth/google/callback (development)
   - https://your-domain.com/auth/google/callback (production)
   - https://your-api-id.execute-api.eu-west-1.amazonaws.com/connections/google/callback (API)
   ```

3. **Save Credentials**
   - Download the JSON file
   - Note the Client ID and Client Secret

---

## 🟦 **Microsoft Outlook OAuth Setup**

### **Step 1: Register Application**

1. **Go to Azure Portal**
   - Visit: https://portal.azure.com/
   - Sign in with Microsoft account

2. **Navigate to App Registrations**
   - Search "App registrations" in the top search bar
   - Click "New registration"

3. **Register Application**
   ```
   Name: Meeting Scheduler
   Supported account types: Accounts in any organizational directory and personal Microsoft accounts
   Redirect URI: Web
   - http://localhost:3000/auth/microsoft/callback (development)
   - https://your-domain.com/auth/microsoft/callback (production)
   ```

### **Step 2: Configure API Permissions**

1. **Add Permissions**
   - Go to "API permissions"
   - Click "Add a permission" → "Microsoft Graph"
   - Select "Delegated permissions"

2. **Required Permissions**
   ```
   Calendars.ReadWrite - Read and write user calendars
   User.Read - Sign in and read user profile
   Mail.Send - Send mail as user (for notifications)
   offline_access - Maintain access to data
   ```

3. **Grant Admin Consent**
   - Click "Grant admin consent" (if you're admin)
   - Or request admin approval

### **Step 3: Create Client Secret**

1. **Go to Certificates & Secrets**
   - Click "New client secret"
   - Description: `Meeting Scheduler Secret`
   - Expires: 24 months (recommended)

2. **Save Secret Value**
   - Copy the secret value immediately
   - Note the Client ID from the Overview page

---

## ⚙️ **Configure Application**

### **Step 1: Update Environment Variables**

Create/update your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth Configuration  
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Frontend Configuration
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
NEXT_PUBLIC_MICROSOFT_CLIENT_ID=your-microsoft-client-id
```

### **Step 2: Store in AWS Secrets Manager** (for production)

```bash
# Store Google OAuth credentials
aws secretsmanager create-secret \
  --name "google-oauth-credentials" \
  --description "Google OAuth client credentials for Meeting Scheduler" \
  --secret-string '{
    "client_id": "your-google-client-id.apps.googleusercontent.com",
    "client_secret": "your-google-client-secret"
  }' \
  --region eu-west-1

# Store Microsoft OAuth credentials
aws secretsmanager create-secret \
  --name "microsoft-oauth-credentials" \
  --description "Microsoft OAuth client credentials for Meeting Scheduler" \
  --secret-string '{
    "client_id": "your-microsoft-client-id",
    "client_secret": "your-microsoft-client-secret"
  }' \
  --region eu-west-1
```

---

## 🧪 **Testing OAuth Integration**

### **Step 1: Test Google OAuth Flow**

```bash
# Start your API server
cd backend
python simple_api_server.py

# Test Google OAuth initiation
curl -X POST http://localhost:8000/connections/google/auth \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uri": "http://localhost:3000/auth/google/callback"
  }'
```

### **Step 2: Test Microsoft OAuth Flow**

```bash
# Test Microsoft OAuth initiation
curl -X POST http://localhost:8000/connections/microsoft/auth \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uri": "http://localhost:3000/auth/microsoft/callback"
  }'
```

### **Step 3: Test Calendar Access**

```bash
# After OAuth completion, test calendar access
curl -X GET http://localhost:8000/calendar/events \
  -H "Authorization: Bearer your-jwt-token"
```

---

## 🔒 **Security Best Practices**

### **Redirect URI Security**
- Always use HTTPS in production
- Validate redirect URIs server-side
- Use state parameter to prevent CSRF attacks

### **Token Management**
- Store refresh tokens encrypted in database
- Implement token rotation
- Set appropriate token expiration times

### **Scopes**
- Request minimal required scopes
- Explain to users why each permission is needed
- Allow users to revoke access

---

## 🚨 **Troubleshooting**

### **Common Google OAuth Issues**

1. **"redirect_uri_mismatch" Error**
   ```
   Solution: Ensure redirect URI in request exactly matches 
   the one configured in Google Cloud Console
   ```

2. **"access_denied" Error**
   ```
   Solution: User denied permission or app not approved.
   Check OAuth consent screen configuration.
   ```

3. **"invalid_client" Error**
   ```
   Solution: Check client ID and secret are correct.
   Ensure they match your Google Cloud project.
   ```

### **Common Microsoft OAuth Issues**

1. **"AADSTS50011" Error**
   ```
   Solution: Redirect URI mismatch. Check Azure app registration
   redirect URIs match your request.
   ```

2. **"AADSTS65001" Error**
   ```
   Solution: User or admin hasn't consented to use the app.
   Grant admin consent in Azure portal.
   ```

3. **"invalid_client" Error**
   ```
   Solution: Check client ID and secret. Ensure secret
   hasn't expired in Azure portal.
   ```

---

## 📋 **OAuth Setup Checklist**

### **Google Setup:**
- [ ] Created Google Cloud project
- [ ] Enabled Calendar and Gmail APIs
- [ ] Configured OAuth consent screen
- [ ] Created OAuth 2.0 credentials
- [ ] Added redirect URIs
- [ ] Noted Client ID and Secret

### **Microsoft Setup:**
- [ ] Registered app in Azure portal
- [ ] Added required API permissions
- [ ] Granted admin consent
- [ ] Created client secret
- [ ] Added redirect URIs
- [ ] Noted Client ID and Secret

### **Application Configuration:**
- [ ] Updated .env file with credentials
- [ ] Stored secrets in AWS Secrets Manager
- [ ] Configured frontend environment variables
- [ ] Tested OAuth flows
- [ ] Verified calendar access

---

## 🎉 **Success!**

Once configured, users will be able to:
- ✅ Connect Google Calendar accounts
- ✅ Connect Microsoft Outlook accounts  
- ✅ View unified calendar availability
- ✅ Schedule meetings across platforms
- ✅ Receive AI-powered scheduling suggestions
- ✅ Get conflict resolution recommendations

**Your OAuth integration is now ready for production use!** 🚀