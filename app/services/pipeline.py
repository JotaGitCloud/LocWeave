"""Pipeline de localización: seis etapas independientes que comparten un contexto.

  1. Ingesta          -> lee el archivo con el manejador de su formato
  2. Segmentación     -> detecta idioma, crea el proyecto y guarda los segmentos
  3. Preprocesamiento -> memoria de traducción, glosario y protección de variables
  4. Traducción       -> proveedor de traducción (intercambiable)
  5. Validación       -> restaura variables, aplica QA y guarda el resultado
  6. Exportación      -> escribe el archivo traducido en el formato original
"""
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..database import Database
from ..languages import detect_language
from ..models import (STATUS_NEEDS_REVIEW, STATUS_PENDING, STATUS_REVIEWED, STATUS_TRANSLATED,
                      Project, Segment)
from ..parsers import ParsedEntry, get_handler
from ..providers.base import TranslationProvider
from . import placeholders
from .validation import has_errors, validate

ProgressFn = Callable[[str, int, int], None]
BATCH_SIZE = 16


class PipelineError(Exception):
    pass


class Cancelled(PipelineError):
    pass


@dataclass
class Work:
    segment: Segment
    masked: str
    mapping: dict
    lead: str
    trail: str
    raw: str = ""


@dataclass
class PipelineContext:
    db: Database
    project: Optional[Project] = None
    source_path: Optional[Path] = None
    name: str = ""
    source_lang: str = "auto"
    target_lang: str = "es"
    entries: List[ParsedEntry] = field(default_factory=list)
    provider: Optional[TranslationProvider] = None
    only_pending: bool = True
    output_path: Optional[Path] = None
    progress: ProgressFn = lambda msg, done, total: None
    cancel: Optional[threading.Event] = None
    work: List[Work] = field(default_factory=list)
    report: Dict[str, int] = field(default_factory=dict)

    def check_cancel(self) -> None:
        if self.cancel is not None and self.cancel.is_set():
            raise Cancelled("Operación cancelada.")


class Stage(ABC):
    name = ""

    @abstractmethod
    def run(self, ctx: PipelineContext) -> None:
        ...


class Pipeline:
    def __init__(self, stages: List[Stage]):
        self.stages = stages

    def run(self, ctx: PipelineContext) -> PipelineContext:
        for stage in self.stages:
            ctx.check_cancel()
            stage.run(ctx)
        return ctx


# ---------------------------------------------------------------- 1. Ingesta
class IngestStage(Stage):
    name = "Ingesta"

    def run(self, ctx: PipelineContext) -> None:
        if ctx.source_path is None or not Path(ctx.source_path).is_file():
            raise PipelineError("El archivo de origen no existe.")
        ctx.progress("Leyendo archivo…", 0, 1)
        ctx.entries = get_handler(ctx.source_path).parse(ctx.source_path)
        if not ctx.entries:
            raise PipelineError("No se encontraron textos traducibles en el archivo.")


# ---------------------------------------------------------------- 2. Segmentación
class SegmentStage(Stage):
    name = "Segmentación"

    def run(self, ctx: PipelineContext) -> None:
        source = ctx.source_lang
        if source == "auto":
            source = detect_language(e.text for e in ctx.entries)
            if source is None:
                raise PipelineError("No se pudo detectar el idioma de origen. Selecciónalo manualmente.")
        if source == ctx.target_lang:
            raise PipelineError("El idioma de origen y el de destino son el mismo.")
        handler = get_handler(ctx.source_path)
        ctx.project = ctx.db.create_project(
            ctx.name or Path(ctx.source_path).stem, source, ctx.target_lang, ctx.source_path, handler.name)
        rows = [(e.key, e.text, e.context, e.existing, STATUS_TRANSLATED if e.existing.strip() else STATUS_PENDING)
                for e in ctx.entries]
        ctx.db.add_segments(ctx.project.id, rows)
        ctx.report["segments"] = len(rows)


# ---------------------------------------------------------------- 3. Preprocesamiento
class PreprocessStage(Stage):
    name = "Preprocesamiento"

    def run(self, ctx: PipelineContext) -> None:
        project = ctx.project
        glossary = ctx.db.list_glossary(project.id)
        segments = ctx.db.list_segments(project.id)
        if ctx.only_pending:
            segments = [s for s in segments if s.status == STATUS_PENDING]
        else:
            segments = [s for s in segments if s.status != STATUS_REVIEWED]
        ctx.work, tm_hits = [], 0
        for seg in segments:
            hit = ctx.db.tm_lookup(project.source_lang, project.target_lang, seg.source_text)
            if hit is not None:
                issues = validate(seg.source_text, hit)
                ctx.db.update_segment(seg.id, hit, STATUS_NEEDS_REVIEW if has_errors(issues) else STATUS_TRANSLATED,
                                      issues)
                tm_hits += 1
                continue
            text = seg.source_text
            body = text.strip()
            lead = text[:len(text) - len(text.lstrip())]
            trail = text[len(text.rstrip()):]
            masked, mapping = placeholders.mask(body, glossary)
            ctx.work.append(Work(seg, masked, mapping, lead, trail))
        ctx.report["tm_hits"] = tm_hits


# ---------------------------------------------------------------- 4. Traducción
class TranslateStage(Stage):
    name = "Traducción"

    def run(self, ctx: PipelineContext) -> None:
        if ctx.provider is None:
            raise PipelineError("No hay un proveedor de traducción seleccionado.")
        if not ctx.work:
            return
        ok, message = ctx.provider.is_available()
        if not ok:
            raise PipelineError(message)
        src, tgt = ctx.project.source_lang, ctx.project.target_lang
        ctx.provider.prepare(src, tgt, ctx.progress)
        total = len(ctx.work)
        for start in range(0, total, BATCH_SIZE):
            ctx.check_cancel()
            batch = ctx.work[start:start + BATCH_SIZE]
            results = ctx.provider.translate_batch([w.masked for w in batch], src, tgt)
            if len(results) != len(batch):
                raise PipelineError("El proveedor devolvió un número distinto de traducciones.")
            for w, r in zip(batch, results):
                w.raw = r
            ctx.progress("Traduciendo…", min(start + BATCH_SIZE, total), total)


# ---------------------------------------------------------------- 5. Validación
class ValidateStage(Stage):
    name = "Validación"

    def run(self, ctx: PipelineContext) -> None:
        translated = review = 0
        for w in ctx.work:
            text, _missing = placeholders.restore(w.raw, w.mapping)
            target = w.lead + text.strip() + w.trail
            issues = validate(w.segment.source_text, target)
            bad = has_errors(issues)
            ctx.db.update_segment(w.segment.id, target, STATUS_NEEDS_REVIEW if bad else STATUS_TRANSLATED, issues)
            review += bad
            translated += not bad
        ctx.report.update(translated=translated, needs_review=review)


# ---------------------------------------------------------------- 6. Exportación
class ExportStage(Stage):
    name = "Exportación"

    def run(self, ctx: PipelineContext) -> None:
        project = ctx.project
        source = Path(project.source_path)
        if not source.is_file():
            raise PipelineError(f"No se encuentra el archivo original: {source}")
        if ctx.output_path is None:
            raise PipelineError("Falta la ruta de salida.")
        translations = {s.key: s.target_text for s in ctx.db.list_segments(project.id) if s.target_text.strip()}
        get_handler(source).export(source, ctx.output_path, translations, project.target_lang)
        ctx.report["exported"] = len(translations)


IMPORT_STAGES = [IngestStage, SegmentStage]
TRANSLATE_STAGES = [PreprocessStage, TranslateStage, ValidateStage]
EXPORT_STAGES = [ExportStage]


def build(stage_classes) -> Pipeline:
    return Pipeline([cls() for cls in stage_classes])
