# Deploying PolicyGPT

| Part | Host | Free plan | Address you get |
|---|---|---|---|
| Backend (FastAPI) | Render | Yes | `https://policygpt-api.onrender.com` |
| Frontend (Next.js) | Vercel | Yes | `https://<project>.vercel.app` |
| Sign-in | Clerk | Yes | - |

## 1. Push the code to GitHub
```
cd C:\policyGPT
git add -A
git commit -m "PolicyGPT: fixes, validation, tests, redesign, deployment config"
git push
```

## 2. Clerk (sign-in)
1. On https://dashboard.clerk.com open (or claim) the application.
2. **API keys**: copy the **Publishable key** (`pk_...`), the **Secret key** (`sk_...`) and the **JWKS URL**.
3. Optional: *User & authentication -> Password* -> set minimum length to 8, and enable Google sign-in.

## 3. Backend on Render
1. https://dashboard.render.com -> **New -> Blueprint** -> choose this repository (it reads `render.yaml`).
2. Fill in when asked:
   - `CLERK_JWKS_URL` = the JWKS URL from Clerk
   - `CORS_ORIGINS` = your Vercel address (add it after step 4, then redeploy)
   - `ADMIN_EMAILS` = your Clerk user id or email
3. Wait for the deploy, then open `https://<your-service>.onrender.com/health` - it should show `"status":"ok"`.

## 4. Frontend on Vercel
1. https://vercel.com/new -> import the repository.
2. **Root Directory**: `frontend` (framework is detected as Next.js).
3. Environment variables:
   - `NEXT_PUBLIC_BACKEND_URL` = the Render address from step 3 (no trailing slash)
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` = `pk_...`
   - `CLERK_SECRET_KEY` = `sk_...`
4. **Deploy**. Copy the Vercel address into Render's `CORS_ORIGINS` and redeploy the backend.
5. In Clerk, add the Vercel address under **Domains / Allowed origins** if it asks.

## Good to know
- **Cold starts**: Render's free plan sleeps after 15 minutes without traffic; the first request then takes 30-60 seconds. Open `/health` a minute before a demo.
- **Data**: the free plan uses a SQLite file that resets on every redeploy or restart; the demo data (21 schemes, sample surveys) is recreated automatically. For permanent data, add a Render PostgreSQL database and set `DATABASE_URL` to its connection string (`postgresql+psycopg://...`).
- **Without an OpenAI key** the assistant runs in offline mode (keyword search over the scheme database). Add `OPENAI_API_KEY` on Render for GPT-4o answers and Hindi/Kannada replies.
