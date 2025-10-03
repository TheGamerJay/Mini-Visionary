#!/bin/bash
# Test authentication endpoints on Railway

API_URL="${1:-https://minivisionary.soulbridgeai.com}"

echo "🧪 Testing secure auth system at $API_URL"
echo ""

# 1. Register a test user
echo "1️⃣ Registering test user..."
REGISTER_RESP=$(curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test'$(date +%s)'@example.com","password":"testpass123"}')

echo "$REGISTER_RESP" | python -m json.tool
echo ""

# 2. Login
echo "2️⃣ Logging in..."
LOGIN_RESP=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}')

TOKEN=$(echo "$LOGIN_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "$LOGIN_RESP" | python -m json.tool
echo ""

# 3. Get user info
echo "3️⃣ Getting user info with token..."
curl -s "$API_URL/api/me" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo ""

# 4. Check credits
echo "4️⃣ User should have 20 starting credits"
echo ""

echo "✅ Test complete! Save the token to test image generation:"
echo "export AUTH_TOKEN='$TOKEN'"
