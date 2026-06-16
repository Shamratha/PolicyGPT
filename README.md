# PolicyGPT

PolicyGPT is an AI-powered public policy navigation SaaS platform designed to simplify access to government schemes, welfare programs, scholarships, startup grants, and public services for Indian citizens. It acts as a conversational advisor and eligibility evaluation auditor to bridge the gap between complex government policy text and citizen access.

---

## System Architecture & Tech Stack

PolicyGPT is designed as a decoupled, micro-service-ready monorepo structured for high scalability, real-time response, and robust security.

```mermaid
graph TD
    subgraph Frontend ["Frontend (Next.js 15 App Router)"]
        UI["Tailwind CSS & shadcn/ui Dashboard"]
        ClerkSDK["Clerk Client SDK"]
        Recharts["Recharts Visualizations"]
    end

    subgraph AuthProvider ["Identity & Auth Platform"]
        Clerk["Clerk SaaS (JWKS / Session Tokens)"]
    end

    subgraph Backend ["Backend API (FastAPI & Python)"]
        AuthMiddleware["Clerk JWT Auth Middleware"]
        API["FastAPI Routers"]
        
        subgraph Services ["Domain Services Layer"]
            Scraper["Scraper Service (HTMLTextExtractor)"]
            Eligibility["Dual-Phase Eligibility Engine"]
            AIService["Conversational RAG (OpenAI / Gemini)"]
            TransService["Translation Service (Kannada/Hindi/English)"]
            PDFGen["ReportLab PDF Compiler"]
        end
        
        subgraph DataStore ["Data & Vector Storage"]
            PostgreSQL[("PostgreSQL / SQLite (SQLAlchemy ORM)")]
            ChromaDB[("ChromaDB Vector Store (Semantic Embeddings)")]
        end
    end

    subgraph External ["External Services"]
        LLM["AI Models (GPT-4o / Gemini 1.5)"]
    end

    %% Interactions
    UI --> ClerkSDK
    ClerkSDK -- Authenticate & Retrieve Token --> Clerk
    UI -- HTTPS Requests + JWT Bearer Token --> AuthMiddleware
    AuthMiddleware -- Verify JWT via JWKS Endpoint --> Clerk
    AuthMiddleware --> API
    
    API --> Services
    Services --> PostgreSQL
    Services --> ChromaDB
    
    AIService -- Query & Context Embeddings --> LLM
    Eligibility -- Contextual Analysis Verification --> LLM
```

### Architectural Component Breakdown

#### 1. Presentation Layer (Frontend)
- **Framework**: Next.js 15 (React 19) utilizing App Router architecture with Turbopack for optimal compilation.
- **Styling & Components**: Tailwind CSS combined with `shadcn/ui` (Radix UI primitives) and Framer Motion for smooth, high-fidelity micro-interactions and transitions.
- **Analytics Visualization**: Recharts for rendering SVG-based charts (bar, line, pie) displaying scheme application volume and regional tracking metrics.

#### 2. Authentication & Identity Management
- **Provider**: Clerk Authentication.
- **Implementation**: Fully integrated client-side header components and a secure backend validation middleware utilizing Clerk's JSON Web Key Sets (JWKS) URL.
- **Session Protection**: Next.js middleware routing rules (`src/proxy.ts`) protect dashboard, profile, and application tracking pages.

#### 3. Core Backend Services (FastAPI)
- **Application Framework**: FastAPI (Python 3.11+), enabling high-performance asynchronous request handling.
- **Dual-Phase Eligibility Engine**:
  - *Phase 1 (Deterministic)*: Compares strict demographic profile parameters (state, age, income limits, gender) against structured SQL constraints.
  - *Phase 2 (Contextual RAG)*: Leverages LLMs to evaluate subjective policy clauses (e.g., educational field focus, specific business goals) for highly accurate matching.
- **Semantic Scraper Pipeline**: Custom `HTMLTextExtractor` robust to layout templates and void HTML tag stack poisoning, parsing startup portals and federal schemes into chunked text.
- **Multilingual Translation Middleware**: Seamless translation layer enabling users to query in Hindi, Kannada, or English.
- **PDF Compiler**: Asynchronous generator powered by ReportLab that formats applicant survey logs into high-resolution documents.

#### 4. Persistence & Data Storage
- **SQL Database**: PostgreSQL (Production) / SQLite (Development) accessed through SQLAlchemy ORM with a Repository design pattern. Tracks user state, demographic profiles, application progress, and dashboard checklist statuses.
- **Vector Search Engine**: ChromaDB, storing chunked government policy documents converted to vector embeddings (1536-dim or 768-dim) for semantic similarity searches.

---

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
