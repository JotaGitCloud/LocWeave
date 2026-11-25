"""Modelos de datos del dominio."""
import json
from dataclasses import dataclass, field
from typing import List

STATUS_PENDING = "pending"
STATUS_TRANSLATED = "translated"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_REVIEWED = "reviewed"

STATUS_LABELS = {
    STATUS_PENDING: "Pendiente",
    STATUS_TRANSLATED: "Traducido",
    STATUS_NEEDS_REVIEW: "Revisar",
    STATUS_REVIEWED: "Revisado",
}


@dataclass
class Issue:
    code: str
    severity: str  # "error" | "warning"
    message: str


@dataclass
class Project:
    id: int
    name: str
    source_lang: str
    target_lang: str
    source_path: str
    file_format: str
    created_at: str


@dataclass
class Segment:
    id: int
    project_id: int
    position: int
    key: str
    source_text: str
    target_text: str = ""
    status: str = STATUS_PENDING
    context: str = ""
    issues: List[Issue] = field(default_factory=list)

    @staticmethod
    def issues_from_json(raw: str) -> List[Issue]:
        try:
            return [Issue(**item) for item in json.loads(raw or "[]")]
        except (ValueError, TypeError):
            return []

    @staticmethod
    def issues_to_json(issues: List[Issue]) -> str:
        return json.dumps([i.__dict__ for i in issues], ensure_ascii=False)
