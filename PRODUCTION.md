# Production Environment Configuration

## Required Environment Variables

### Core Application
```bash
# Strong random secret for sessions
SECRET_KEY=your-strong-random-secret-key

# Database connection (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@host:port/database

# Public app URL for password reset links
PUBLIC_APP_URL=https://your-app-domain.com
```

### Email Service (Resend)
```bash
# Resend API key for email sending
RESEND_API_KEY=re_your_resend_api_key

# Sender email addresses
FROM_EMAIL=support@minidreamposter.com
RESEND_FROM=noreply@minidreamposter.com
FROM_NAME="Mini Dream Poster"
```

### CORS and Security (HTTPS)
```bash
# Comma-separated list of allowed frontend origins (HTTPS required)
CORS_ORIGINS=https://your-frontend-domain.com,https://app.minidreamposter.com

# Enable secure cookies for HTTPS (required for production)
SESSION_COOKIE_SECURE=True

# Production environment flag
FLASK_ENV=production

# For cross-domain setups (if frontend/backend on different domains)
# SESSION_COOKIE_SAMESITE=None
```

### AI Service
```bash
# OpenAI API key for poster generation
OPENAI_API_KEY=sk-your-openai-api-key
```

## E2E Smoke Tests

Replace `<host>` with your actual domain:

### 1. Who am I (logged out → null)
```bash
curl -i https://<host>/api/auth/whoami
```

### 2. Register (auto-login, credits granted)
```bash
curl -i https://<host>/api/auth/register \
  -H "Content-Type: application/json" \
  -c cookies.txt -b cookies.txt \
  -d '{"email":"your-email@example.com","password":"YourSecurePassword","display_name":"Your Name"}'
```

### 3. Who am I (now logged in)
```bash
curl -i https://<host>/api/auth/whoami -c cookies.txt -b cookies.txt
```

### 4. Logout
```bash
curl -i https://<host>/api/auth/logout -X POST -c cookies.txt -b cookies.txt
```

### 5. Forgot password (non-disclosing)
```bash
curl -i https://<host>/api/auth/forgot \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com"}'
```

### 6. Health checks
```bash
curl -i https://<host>/healthz
curl -i https://<host>/api/version
```

## Frontend Type Definitions

Ensure your React components use the correct types:

```typescript
type WhoAmI = {
  id: number;
  email: string;
  display_name?: string;
  avatar_url?: string;
} | null;
```

## Security Checklist

- ✅ All fetch calls use `credentials: 'include'`
- ✅ CORS origins properly configured
- ✅ Session cookies secured with HTTPS in production
- ✅ Password reset tokens have proper expiry validation
- ✅ Single transaction for user registration + credit bonus
- ✅ Consistent data shapes across all auth endpoints

## Cross-Domain Setup (if needed)

If frontend and backend are on different domains:

```bash
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True  # HTTPS required
```

## Optional Enhancements

### Rate Limiting
- Consider per-endpoint rate limits
- Add login throttling for brute force protection

### Audit Fields
- Add `accepted_terms_at` timestamp to User model
- Track login/logout events for security auditing

### CSRF Protection
- Add CSRF tokens to any HTML forms (if using Flask-WTF)