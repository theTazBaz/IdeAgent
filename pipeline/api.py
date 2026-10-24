"""
pipeline/api.py
===============
FastAPI server: POST /api/search runs the agentic RAG pipeline, and the
React frontend (frontend/dist, built with `npm run build`) is served from /.

    uvicorn pipeline.api:app --reload

The embedding model is loaded once at startup so the first question is not slow.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pipeline import embed
from pipeline.llm import LLMError
from pipeline.rag import run_rag_data

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(embed._get_model)
    yield


app = FastAPI(title="IdeAgent", lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)


@app.post("/api/search")
async def search(req: SearchRequest) -> dict:
    try:
        return await run_in_threadpool(run_rag_data, req.query.strip())
    except LLMError as exc:
        headers = {"Retry-After": str(int(exc.retry_after) + 1)} if exc.retry_after else None
        raise HTTPException(exc.status_code, exc.user_message, headers=headers)
    except Exception as exc:  # surface pipeline errors to the UI
        raise HTTPException(500, f"{type(exc).__name__}: {exc}")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


if (DIST_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")


@app.get("/", response_model=None)
def index():
    page = DIST_DIR / "index.html"
    if page.is_file():
        return FileResponse(page)
    return HTMLResponse(
        "<p>Frontend not built. Run <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code>, "
        "or use <code>npm run dev</code> for development.</p>",
        status_code=503,
    )
