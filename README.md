# PolicyGPT

PolicyGPT is an AI-powered public policy navigation SaaS platform designed to simplify access to government schemes, welfare programs, scholarships, startup grants, and public services for Indian citizens. It acts as a conversational advisor and eligibility evaluation auditor to bridge the gap between complex government policy text and citizen access.

---

## Architecture & Tech Stack

The platform is built as a decoupled monorepo:
- **Backend**: FastAPI, SQLAlchemy (PostgreSQL), ChromaDB (Vector Search), OpenAI API (GPT-4o & Text Embeddings), ReportLab (PDF compiling).
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui styles, Framer Motion, Recharts.
- **Authentication**: Clerk Authentication.
- **Orchestration**: Docker Compose.

---

## Core Features

1. **AI Policy Assistant**: Grounded Conversational RAG interface (GPT-4o) with citation tracking and confidence scores.
2. **Structured Eligibility Engine**: Multi-phase criteria checker:
   - *Phase 1*: Deterministic comparison validation of age limits, state, gender, and income parameters.
   - *Phase 2*: LLM contextual verification for advanced clauses (e.g. business goals, education fields).
3. **Interactive Dashboard**: Track started application progress, check off required document checklists, and review eligible matches.
4. **Impact & Bottlenecks Analytics**: Visual reporting dashboard tracking scheme requests, regional awareness, and filing bottlenecks.
5. **PDF Report Generator**: Compiles survey logs and demographic bottlenecks into a professional, downloadable "Policy Access Report" PDF.
6. **Multilingual Support**: Supports Karnataka (Kannada), Hindi, and English query inputs with a seamless LLM translation middleware.

---

## Folder Structure

```
policyGPT/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy Models (User, Profile, Scheme, Survey, Analytics)
│   │   ├── schemas/       # Pydantic schemas (validation)
│   │   ├── repositories/  # Repository pattern implementation
│   │   ├── services/      # AI, translation, report, and eligibility services
│   │   ├── routers/       # FastAPI route endpoints
│   │   ├── utils/         # Seeding, Auth verification, logging helpers
│   │   └── main.py        # Entrypoint
│   ├── tests/             # Pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # App Router pages (Landing, Profile, Chat, Explorer, Dashboard, Admin, Surveys)
│   │   ├── components/    # Navbar, Footer, Recharts components
│   │   ├── services/      # Axios client pointing to API
│   │   └── lib/
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml     # Multi-container orchestrator
```

---

## Environment Configuration

Create a `.env` file inside the `backend` and `frontend` directories.

### Backend `.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/policygpt
CHROMA_PERSIST_DIR=./chroma_db
OPENAI_API_KEY=your-openai-api-key
CLERK_JWKS_URL=https://api.clerk.com/v1/jwks
ENVIRONMENT=development
PORT=8000
```

### Frontend `.env`:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

---

## Getting Started

### 1. Running via Docker Compose (Recommended)

To spin up all services (PostgreSQL Database, FastAPI Backend, Next.js Frontend) in one command:
```bash
docker-compose up --build
```
The services will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

---

### 2. Running Locally for Development

#### Backend Setup:
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Initialize virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
   pip install -r requirements.txt
   ```
4. Run migrations and seed data (pre-populates central & Karnataka schemes, rules, and mock survey entries):
   ```bash
   PYTHONPATH=. python app/utils/seed_data.py
   ```
5. Launch FastAPI development server:
   ```bash
   PYTHONPATH=. uvicorn app.main:app --reload
   ```

#### Frontend Setup:
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Start Next.js development server:
   ```bash
   npm run dev
   ```

---

## Running Verification Tests

To run the automated test suite checking the eligibility parser, translation fallbacks, and PDF compiler:
```bash
cd backend
PYTHONPATH=. .venv/bin/pytest tests/
```
