"""Fachada de la lógica de negocio: la usan la interfaz gráfica y la línea de comandos."""
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..database import Database
from ..models import (STATUS_NEEDS_REVIEW, STATUS_REVIEWED, Issue, Project, Segment)
from ..providers import get_provider
from . import pipeline
from .pipeline import PipelineContext, PipelineError, ProgressFn
from .validation import has_errors, validate


def _noop(msg: str, done: int, total: int) -> None:
    pass


class LocWeaveService:
    def __init__(self, db: Database):
        self.db = db

    # ---- proyectos
    def import_file(self, path, name: str = "", source_lang: str = "auto", target_lang: str = "es",
                    progress: ProgressFn = _noop) -> Project:
        ctx = PipelineContext(db=self.db, source_path=Path(path), name=name, source_lang=source_lang,
                              target_lang=target_lang, progress=progress)
        pipeline.build(pipeline.IMPORT_STAGES).run(ctx)
        return ctx.project

    def list_projects(self) -> List[Project]:
        return self.db.list_projects()

    def get_project(self, project_id: int) -> Project:
        project = self.db.get_project(project_id)
        if project is None:
            raise PipelineError(f"No existe el proyecto {project_id}.")
        return project

    def delete_project(self, project_id: int) -> None:
        self.db.delete_project(project_id)

    def segments(self, project_id: int) -> List[Segment]:
        return self.db.list_segments(project_id)

    def stats(self, project_id: int) -> Dict[str, int]:
        return self.db.project_stats(project_id)

    def set_languages(self, project_id: int, source_lang: str, target_lang: str) -> None:
        if source_lang == target_lang:
            raise PipelineError("El idioma de origen y el de destino son el mismo.")
        self.db.update_project_langs(project_id, source_lang, target_lang)

    # ---- traducción
    def translate(self, project_id: int, provider_name: str, only_pending: bool = True,
                  progress: ProgressFn = _noop, cancel: Optional[threading.Event] = None) -> Dict[str, int]:
        ctx = PipelineContext(db=self.db, project=self.get_project(project_id), provider=get_provider(provider_name),
                              only_pending=only_pending, progress=progress, cancel=cancel)
        pipeline.build(pipeline.TRANSLATE_STAGES).run(ctx)
        return ctx.report

    def prepare_languages(self, provider_name: str, source_lang: str, target_lang: str,
                          progress: ProgressFn = _noop) -> None:
        get_provider(provider_name).prepare(source_lang, target_lang, progress)

    def save_translation(self, segment_id: int, text: str) -> Tuple[Segment, List[Issue]]:
        """Guarda una edición manual: valida y, si no hay errores, la marca como revisada."""
        seg = self.db.get_segment(segment_id)
        if seg is None:
            raise PipelineError("El segmento no existe.")
        project = self.get_project(seg.project_id)
        issues = validate(seg.source_text, text)
        if has_errors(issues):
            status = STATUS_NEEDS_REVIEW
        else:
            status = STATUS_REVIEWED
            self.db.tm_store(project.source_lang, project.target_lang, seg.source_text, text)
        self.db.update_segment(segment_id, text, status, issues)
        return self.db.get_segment(segment_id), issues

    # ---- glosario
    def glossary(self, project_id: int) -> Dict[str, str]:
        return self.db.list_glossary(project_id)

    def add_term(self, project_id: int, term: str, translation: str) -> None:
        if term.strip() and translation.strip():
            self.db.set_glossary_term(project_id, term.strip(), translation.strip())

    def remove_term(self, project_id: int, term: str) -> None:
        self.db.delete_glossary_term(project_id, term)

    # ---- exportación
    def export(self, project_id: int, output_path) -> Dict[str, int]:
        ctx = PipelineContext(db=self.db, project=self.get_project(project_id), output_path=Path(output_path))
        pipeline.build(pipeline.EXPORT_STAGES).run(ctx)
        return ctx.report
