# 🔐 OAuth Quick Reference Card

## 🚀 **Quick Setup Commands**

```bash
# Run interactive OAuth setup
python setup_oauth.py

# Or manually update .env file with your credentials
```

---

## 🟦 **Google OAuth - Quick Steps**

1. **Go to:** https://console.cloud.google.com/
2. **Create project** → Enable Calendar API
3. **OAuth consent screen** → External → Add scopes
4. **Credentials** → Create OAuth 2.0 Client ID
5. **Add redirect URIs:**
   - `http://localhost:3000/auth/google/callback`
   - `https://your-domain.com/auth/google/callback`

**Required Scopes:**
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/calendar.events`
- `https://www.googleapis.com/auth/userinfo.email`

---

## 🟦 **Microsoft OAuth - Quick Steps**

1. **Go to:** https://portal.azure.com/
2. **App registrations** → New registration
3. **API permissions** → Microsoft Graph → Delegated
4. **Certificates & secrets** → New client secret
5. **Add redirect URIs:**
   - `http://localhost:3000/auth/microsoft/callback`
   - `https://your-domain.com/auth/microsoft/callback`

**Required Permissions:**
- `Calendars.ReadWrite`
- `User.Read`
- `Mail.Send`
- `offline_access`

---

## ⚙️ **Environment Variables**

```bash
# Backend (.env)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Frontend (.env.local)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
NEXT_PUBLIC_MICROSOFT_CLIENT_ID=your-microsoft-client-id
```

---

## 🧪 **Testing OAuth**

```bash
# Test Google OAuth flow
curl -X POST http://localhost:8000/connections/google/auth \
  -H "Content-Type: application/json" \
  -d '{"redirect_uri": "http://localhost:3000/auth/google/callback"}'

# Test Microsoft OAuth flow  
curl -X POST http://localhost:8000/connections/microsoft/auth \
  -H "Content-Type: application/json" \
  -d '{"redirect_uri": "http://localhost:3000/auth/microsoft/callback"}'
```

---

## 🚨 **Common Issues**

| Error | Solution |
|-------|----------|
| `redirect_uri_mismatch` | Check redirect URIs match exactly |
| `access_denied` | User denied or app not approved |
| `invalid_client` | Check client ID/secret are correct |
| `insufficient_scope` | Add required permissions/scopes |

---

## 🎯 **Success Checklist**

- [ ] Google Cloud project created
- [ ] Calendar API enabled
- [ ] OAuth consent screen configured
- [ ] Google OAuth credentials created
- [ ] Azure app registration created
- [ ] Microsoft Graph permissions added
- [ ] Client secrets created
- [ ] Redirect URIs configured
- [ ] Environment variables updated
- [ ] OAuth flows tested

**Ready for calendar integration!** 🎉