import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.database.models import Paper

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Papers Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arxiv_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                url TEXT NOT NULL,
                paper_type TEXT NOT NULL,
                summary TEXT,
                problem TEXT,
                method TEXT,
                conclusion TEXT,
                formatted_post TEXT,
                is_published INTEGER DEFAULT 0,
                published_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Classic Queue Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS classic_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arxiv_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                url TEXT NOT NULL,
                published_year INTEGER,
                description TEXT,
                is_processed INTEGER DEFAULT 0,
                processed_at TEXT
            );
            """)
            conn.commit()
            logger.info("SQLite database tables initialized successfully.")

    def seed_classic_papers(self, seed_path: Path):
        seed_path = Path(seed_path)
        if not seed_path.exists():
            logger.warning(f"Seed file not found at {seed_path}")
            return

        with open(seed_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            inserted_count = 0
            for item in items:
                try:
                    cursor.execute("""
                    INSERT OR IGNORE INTO classic_queue (arxiv_id, title, authors, url, published_year, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        item.get("arxiv_id"),
                        item.get("title"),
                        item.get("authors"),
                        item.get("url"),
                        item.get("published_year"),
                        item.get("description")
                    ))
                    if cursor.rowcount > 0:
                        inserted_count += 1
                except Exception as e:
                    logger.error(f"Error seeding item {item.get('arxiv_id')}: {e}")
            conn.commit()
            logger.info(f"Seeded {inserted_count} new classic papers into classic_queue.")

    def is_arxiv_exists(self, arxiv_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM papers WHERE arxiv_id = ?", (arxiv_id,))
            return cursor.fetchone() is not None

    def get_next_classic_paper(self) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM classic_queue 
            WHERE is_processed = 0 
            ORDER BY id ASC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def save_paper(self, paper: Paper) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO papers (arxiv_id, title, authors, url, paper_type, summary, problem, method, conclusion, formatted_post, is_published, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(arxiv_id) DO UPDATE SET
                summary=excluded.summary,
                problem=excluded.problem,
                method=excluded.method,
                conclusion=excluded.conclusion,
                formatted_post=excluded.formatted_post,
                is_published=excluded.is_published,
                published_at=excluded.published_at
            """, (
                paper.arxiv_id,
                paper.title,
                paper.authors,
                paper.url,
                paper.paper_type,
                paper.summary,
                paper.problem,
                paper.method,
                paper.conclusion,
                paper.formatted_post,
                1 if paper.is_published else 0,
                paper.published_at
            ))
            conn.commit()
            return cursor.lastrowid

    def mark_classic_processed(self, arxiv_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
            UPDATE classic_queue SET is_processed = 1, processed_at = ? WHERE arxiv_id = ?
            """, (now, arxiv_id))
            conn.commit()

    def mark_published(self, arxiv_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
            UPDATE papers SET is_published = 1, published_at = ? WHERE arxiv_id = ?
            """, (now, arxiv_id))
            conn.commit()

    def search_papers(
        self,
        query: str = "",
        paper_type: str = "all",
        is_published: Optional[str] = "all",
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if query:
                q_param = f"%{query.strip()}%"
                conditions.append("(arxiv_id LIKE ? OR title LIKE ? OR authors LIKE ? OR summary LIKE ? OR problem LIKE ? OR method LIKE ? OR conclusion LIKE ?)")
                params.extend([q_param] * 7)

            if paper_type in ("classic", "latest"):
                conditions.append("paper_type = ?")
                params.append(paper_type)

            if is_published in ("true", "1"):
                conditions.append("is_published = 1")
            elif is_published in ("false", "0"):
                conditions.append("is_published = 0")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # Count total matching rows
            count_sql = f"SELECT COUNT(*) FROM papers {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]

            # Fetch rows
            select_sql = f"""
            SELECT * FROM papers
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """
            cursor.execute(select_sql, params + [limit, offset])
            rows = [dict(row) for row in cursor.fetchall()]

            return {
                "total": total,
                "items": rows,
                "limit": limit,
                "offset": offset
            }

    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers WHERE arxiv_id = ?", (arxiv_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_paper_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM papers")
            total_papers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM papers WHERE paper_type = 'classic'")
            classic_processed = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM papers WHERE paper_type = 'latest'")
            latest_processed = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM papers WHERE is_published = 1")
            published_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM classic_queue")
            total_classic_queue = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM classic_queue WHERE is_processed = 1")
            classic_queue_processed = cursor.fetchone()[0]

            return {
                "total_papers": total_papers,
                "classic_processed": classic_processed,
                "latest_processed": latest_processed,
                "published_count": published_count,
                "classic_queue_total": total_classic_queue,
                "classic_queue_processed": classic_queue_processed
            }

