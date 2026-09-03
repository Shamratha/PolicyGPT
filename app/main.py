from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agents import PolicyGPTOrchestrator
from .config import settings
from .models import DocumentIn, QueryRequest
from .retrieval import HybridRetriever
from .storage import Store


def build_app() -> FastAPI:
    app = FastAPI(title="PolicyGPT", version="0.1.0", description="Evidence-grounded government-scheme assistance prototype")
    store = Store(settings.db_path)
    retriever = HybridRetriever.from_json(settings.corpus_path)
    orchestrator = PolicyGPTOrchestrator(retriever, settings)
    settings.report_dir.mkdir(parents=True, exist_ok=True)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "documents": len(retriever.documents), "version": app.version}

    @app.post("/api/query")
    def query(request: QueryRequest) -> dict:
        result = orchestrator.run(request)
        sid = store.save_session(request.role, request.query, result)
        result["session_id"] = sid
        route = orchestrator.router.route(request.query)
        audits = [type("Audit", (), a) for a in result["claim_audit"]]
        report = orchestrator.reporter.format_markdown(request, route, result["answer"], result["citations"], audits)
        (settings.report_dir / f"{sid}.md").write_text(report)
        return result

    @app.get("/api/sessions")
    def sessions() -> list[dict]:
        return store.recent_sessions()

    @app.get("/api/reports/{session_id}")
    def report(session_id: str):
        path = settings.report_dir / f"{session_id}.md"
        if not path.exists(): raise HTTPException(status_code=404, detail="Report not found")
        return FileResponse(path, media_type="text/markdown", filename=path.name)

    @app.post("/api/documents")
    def add_document(document: DocumentIn) -> dict[str, str]:
        did = store.save_document(document.model_dump())
        return {"id": did, "message": "Stored. Restart the prototype to include it in retrieval."}

    static = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def home():
        return FileResponse(static / "index.html")

    return app


app = build_app()
