import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config.settings import settings
from src.database.db_manager import DBManager

logger = logging.getLogger("PaperSnapWeb")
db = DBManager(settings.DB_PATH)

app = FastAPI(
    title="Paper Snap Reader & Search Portal",
    description="Interactive web portal to search and read AI paper summaries in SQLite DB.",
    version="1.0.0"
)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WEB_DIR = BASE_DIR / "web"

@app.get("/api/papers")
def search_papers(
    q: str = Query("", description="Keyword search query"),
    paper_type: str = Query("all", description="Paper type filter: all, classic, latest"),
    is_published: str = Query("all", description="Published status: all, true, false"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Search and filter papers in SQLite database.
    """
    results = db.search_papers(
        query=q,
        paper_type=paper_type,
        is_published=is_published,
        limit=limit,
        offset=offset
    )
    return results

@app.get("/api/papers/{arxiv_id}")
def get_paper_detail(arxiv_id: str):
    """
    Get full paper details by ArXiv ID.
    """
    paper = db.get_paper_by_arxiv_id(arxiv_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@app.get("/api/stats")
def get_stats():
    """
    Get database dashboard statistics.
    """
    return db.get_paper_stats()

# Mount Static Files for Web UI
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/")
    def read_root():
        index_path = WEB_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Paper Snap Web UI active. Static index.html not found."}
