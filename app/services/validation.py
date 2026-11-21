"""Etapa de validación (QA) de traducciones."""
from typing import List

from ..models import Issue
from .placeholders import extract_placeholders


def validate(source: str, target: str) -> List[Issue]:
    issues: List[Issue] = []
    if not target.strip():
        return [Issue("empty", "error", "La traducción está vacía.")]

    src_ph, tgt_ph = extract_placeholders(source), extract_placeholders(target)
    missing = src_ph - tgt_ph
    extra = tgt_ph - src_ph
    if missing:
        shown = ", ".join(repr(k) for k in missing)
        issues.append(Issue("placeholder_missing", "error", f"Faltan variables o etiquetas: {shown}"))
    if extra:
        shown = ", ".join(repr(k) for k in extra)
        issues.append(Issue("placeholder_extra", "error", f"Sobran variables o etiquetas: {shown}"))

    if source.count("\n") != target.count("\n"):
        issues.append(Issue("newlines", "warning", "Cambió el número de saltos de línea."))
    if source[:1].isspace() != target[:1].isspace() or source[-1:].isspace() != target[-1:].isspace():
        issues.append(Issue("whitespace", "warning", "Cambiaron los espacios al inicio o al final."))
    if len(source) >= 8 and len(target) > 2.5 * len(source):
        issues.append(Issue("length", "warning", "La traducción es mucho más larga que el original."))
    if len(source) >= 8 and source.strip() == target.strip():
        issues.append(Issue("untranslated", "warning", "El texto quedó igual que el original."))
    return issues


def has_errors(issues: List[Issue]) -> bool:
    return any(i.severity == "error" for i in issues)
