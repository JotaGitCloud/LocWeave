"""Capa de persistencia con SQLite (biblioteca estándar)."""
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .models import Issue, Project, Segment

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    source_path TEXT NOT NULL,
    file_format TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    key TEXT NOT NULL,
    source_text TEXT NOT NULL,
    target_text TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    context TEXT NOT NULL DEFAULT '',
    issues TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_segments_project ON segments(project_id, position);
CREATE TABLE IF NOT EXISTS glossary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    term TEXT NOT NULL,
    translation TEXT NOT NULL,
    UNIQUE(project_id, term)
);
CREATE TABLE IF NOT EXISTS translation_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    source_text TEXT NOT NULL,
    target_text TEXT NOT NULL,
    UNIQUE(source_lang, target_lang, source_text)
);
"""


class Database:
    def __init__(self, path):
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ---------------- proyectos ----------------
    def create_project(self, name, source_lang, target_lang, source_path, file_format) -> Project:
        now = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO projects(name, source_lang, target_lang, source_path, file_format, created_at)"
                " VALUES (?,?,?,?,?,?)",
                (name, source_lang, target_lang, str(source_path), file_format, now),
            )
            self._conn.commit()
            return self.get_project(cur.lastrowid)

    @staticmethod
    def _project(row) -> Project:
        return Project(**{k: row[k] for k in row.keys()})

    def get_project(self, project_id: int) -> Optional[Project]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return self._project(row) if row else None

    def list_projects(self) -> List[Project]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        return [self._project(r) for r in rows]

    def update_project_langs(self, project_id: int, source_lang: str, target_lang: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE projects SET source_lang=?, target_lang=? WHERE id=?",
                (source_lang, target_lang, project_id),
            )
            self._conn.commit()

    def delete_project(self, project_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
            self._conn.commit()

    # ---------------- segmentos ----------------
    @staticmethod
    def _segment(row) -> Segment:
        return Segment(
            id=row["id"], project_id=row["project_id"], position=row["position"],
            key=row["key"], source_text=row["source_text"], target_text=row["target_text"],
            status=row["status"], context=row["context"],
            issues=Segment.issues_from_json(row["issues"]),
        )

    def add_segments(self, project_id: int, rows: List[Tuple[str, str, str, str, str]]) -> None:
        """rows: (key, source_text, context, target_text, status)"""
        with self._lock:
            self._conn.executemany(
                "INSERT INTO segments(project_id, position, key, source_text, context, target_text, status)"
                " VALUES (?,?,?,?,?,?,?)",
                [(project_id, i, k, s, c, t, st) for i, (k, s, c, t, st) in enumerate(rows)],
            )
            self._conn.commit()

    def list_segments(self, project_id: int, status: Optional[str] = None) -> List[Segment]:
        sql = "SELECT * FROM segments WHERE project_id=?"
        args: list = [project_id]
        if status:
            sql += " AND status=?"
            args.append(status)
        sql += " ORDER BY position"
        with self._lock:
            rows = self._conn.execute(sql, args).fetchall()
        return [self._segment(r) for r in rows]

    def get_segment(self, segment_id: int) -> Optional[Segment]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM segments WHERE id=?", (segment_id,)).fetchone()
        return self._segment(row) if row else None

    def update_segment(self, segment_id: int, target_text: str, status: str, issues: List[Issue]) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE segments SET target_text=?, status=?, issues=? WHERE id=?",
                (target_text, status, Segment.issues_to_json(issues), segment_id),
            )
            self._conn.commit()

    def project_stats(self, project_id: int) -> Dict[str, int]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT status, COUNT(*) AS n FROM segments WHERE project_id=? GROUP BY status",
                (project_id,),
            ).fetchall()
        stats = {r["status"]: r["n"] for r in rows}
        stats["total"] = sum(stats.values())
        return stats

    # ---------------- glosario ----------------
    def set_glossary_term(self, project_id: int, term: str, translation: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO glossary(project_id, term, translation) VALUES (?,?,?)"
                " ON CONFLICT(project_id, term) DO UPDATE SET translation=excluded.translation",
                (project_id, term, translation),
            )
            self._conn.commit()

    def list_glossary(self, project_id: int) -> Dict[str, str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT term, translation FROM glossary WHERE project_id=? ORDER BY term", (project_id,)
            ).fetchall()
        return {r["term"]: r["translation"] for r in rows}

    def delete_glossary_term(self, project_id: int, term: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM glossary WHERE project_id=? AND term=?", (project_id, term))
            self._conn.commit()

    # ---------------- memoria de traducción ----------------
    def tm_lookup(self, source_lang: str, target_lang: str, source_text: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT target_text FROM translation_memory WHERE source_lang=? AND target_lang=? AND source_text=?",
                (source_lang, target_lang, source_text),
            ).fetchone()
        return row["target_text"] if row else None

    def tm_store(self, source_lang: str, target_lang: str, source_text: str, target_text: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO translation_memory(source_lang, target_lang, source_text, target_text)"
                " VALUES (?,?,?,?) ON CONFLICT(source_lang, target_lang, source_text)"
                " DO UPDATE SET target_text=excluded.target_text",
                (source_lang, target_lang, source_text, target_text),
            )
            self._conn.commit()
