# Mini-Visionary — Setup

*You Envision it, We Generate it*

---

## 1) Requirements

- Python 3.10+
- Node 18+ (only if you’ll use the separate Vite frontend; the Flask inline UI works without it)
- Git
- (Optional) OpenAI API key for image generation (`gpt-image-1`)

---

## 2) Clone

```bash
git clone https://github.com/<you>/mini-dream-poster.git
cd mini-dream-poster
```

---

## 3) Backend (Flask API)

Create a virtualenv and install deps:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```bash
cp .env.example .env
```

Fill in values:

```
SECRET_KEY=change-me
OPENAI_API_KEY=sk-...         # optional; leave blank to use placeholder images
UPLOAD_DIR=./uploads          # local save path
MAX_UPLOAD_MB=20              # reject files > N MB
RATE_LIMIT_WINDOW_SEC=30
RATE_LIMIT_MAX_REQUESTS=6
```

Run the API:

```bash
python app.py
```

Open: [http://localhost:8080/](http://localhost:8080/) → you should see the Mini Dream Poster page.

---

## 4) Frontend (optional Vite app)

If you’re using the `/frontend` app (monorepo structure):

```bash
cd ../frontend
npm install
npm run dev
```

Set `VITE_API_BASE` in `frontend/.env` if your API runs on another host/port.

---

## 5) Deploy on Railway

- Push to GitHub.
- In Railway: **New Project → Deploy from GitHub** → select this repo.
- Railway reads `railway.toml` and creates:
  - **backend** (Flask)
  - **frontend** (Vite) — optional if you keep the inline Flask UI
- Add env vars to the **backend** service:
  - `SECRET_KEY`
  - `OPENAI_API_KEY` *(optional)*
  - `UPLOAD_DIR=/app/uploads`

Deploy.

Health check: `https://<backend-domain>/api/health`  
UI: `https://<backend-domain>/` (inline page) or your frontend domain if using Vite.

⚠️ Note: Railway’s filesystem is ephemeral—fine for MVP. For production, switch `/uploads` to S3/Cloudflare R2 and return signed URLs.

---

## 6) API Reference

### POST `/api/poster/generate`
Create a poster via **text→poster** (prompt only) or **image→poster** (upload + prompt).

Form fields:
- `prompt` *(optional)*
- `style` *(optional, e.g., “fantasy key art, cinematic, vivid”)*
- `title` *(optional overlay)*
- `tagline` *(optional overlay)*
- `image` *(optional file upload: png/jpg/webp)*

Response:

```json
{
  "ok": true,
  "mode": "text_to_poster" | "image_to_poster",
  "title": "...",
  "tagline": "...",
  "url": "/uploads/poster_2025...png",
  "used_openai": true
}
```

---

### POST `/api/poster/add-text`
Add/replace cinematic title + tagline on an existing poster.

**Body (JSON):**
```json
{ "url": "/uploads/poster_...", "title": "MY TITLE", "tagline": "My tagline" }
```

**Response:**
```json
{ "ok": true, "url": "/uploads/poster_..._titled.png" }
```

---

### GET `/uploads/<filename>`
Serves generated images.

### GET `/api/health` and `/healthz`
Basic health checks.

---

## 7) Storage (Production)

By default, posters are saved in `/uploads` locally (Railway ephemeral).

For persistent storage, enable **S3/R2**:

1. Create a Cloudflare R2 bucket (or AWS S3).  
2. Add env vars to the backend service:

```
BUCKET_ENABLED=true
BUCKET_NAME=<bucket-name>
BUCKET_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
BUCKET_REGION=auto
BUCKET_KEY=<r2-access-key>
BUCKET_SECRET=<r2-secret>
```

3. The backend will automatically upload generated posters to your bucket and return public URLs.

---

## 8) Security & Limits

- Basic IP rate limit via env:
  - `RATE_LIMIT_WINDOW_SEC`, `RATE_LIMIT_MAX_REQUESTS`
- File validation: only `png/jpg/jpeg/webp`, size capped by `MAX_UPLOAD_MB`
- Add a reverse proxy (Railway default) + HTTPS.

---

## 9) License

This project ships with **Mini Dream Poster License (MIT + NonCommercial + User Liability)** in `LICENSE`.

- Personal/educational use allowed.  
- No commercial use without permission.  
- Users are responsible for complying with copyright/IP laws.  
- No warranty.

---

## 10) Troubleshooting

- **“used_openai: false”** → You didn’t set `OPENAI_API_KEY` or the `openai` lib isn’t installed. Install deps and set the key.  
- **Images don’t show in prod** → Ensure `UPLOAD_DIR` exists and is writable, or switch to S3/R2.  
- **CORS issues** → Flask enables CORS. If you use a separate frontend domain, verify `VITE_API_BASE` and proxy settings.  
- **Railway build fails** → Check `requirements.txt` versions and Python runtime. Add a `Procfile` if needed:  
  ```
  web: python app.py
  ```

---

## 11) Roadmap (nice-to-have)

- S3/R2 storage + CDN  
- Queued jobs (Redis/Upstash) for heavy batches  
- Real upscaling (ESRGAN/Replicate/RunPod)  
- Auth + user libraries (Postgres)  
- Style presets & templates  

---

# Mini Dream Poster — Commercial License

This Commercial License Agreement ("Agreement") is entered into between:

**Licensor**: TheGamerJay (the "Author")  
**Licensee**: [Customer/Company Name]  

---

### 1. Grant of License
The Licensor grants the Licensee a non-exclusive, worldwide, non-transferable license to use the **Mini Dream Poster** software (the "Software") for **commercial purposes**, including but not limited to:
- Hosting the Software as part of a SaaS product
- Distributing, sublicensing, or integrating the Software into a commercial product
- Monetizing services built on top of the Software

---

### 2. Restrictions
The Licensee shall not:
- Remove or alter copyright notices
- Misrepresent authorship or origin of the Software
- Use the Software for unlawful purposes

---

### 3. Attribution
The Licensee must include clear attribution in documentation or about pages:

```
Powered by Mini Dream Poster — © 2025 TheGamerJay
```

---

### 4. Payment
This license is only valid upon full payment of the agreed commercial licensing fee.  
Licensor reserves the right to revoke this license if payment is not completed.

---

### 5. Warranty Disclaimer
The Software is provided "AS IS", without warranty of any kind.  
Licensor shall not be held liable for damages arising from its use.

---

### 6. Termination
If the Licensee breaches this Agreement, the License will automatically terminate.  

---

**Signed:**  
TheGamerJay  
Date: ____________

**Accepted by Licensee:**  
Company/Name: ____________  
Signature: ____________  
Date: ____________