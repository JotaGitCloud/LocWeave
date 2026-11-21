"""Idiomas soportados y detección aproximada del idioma de origen (sin dependencias)."""
import re
from collections import Counter
from typing import Iterable, Optional

LANGUAGES = {
    "es": "Español",
    "en": "Inglés",
    "ja": "Japonés",
    "zh": "Chino",
    "ko": "Coreano",
    "fr": "Francés",
    "de": "Alemán",
    "pt": "Portugués",
    "it": "Italiano",
    "ru": "Ruso",
}

_STOPWORDS = {
    "en": "the and you to of is in it that for with are this what not have".split(),
    "es": "el la de que y en los un una es por con para no se te tu las del".split(),
    "fr": "le les des est et vous je une pas que pour dans qui sur".split(),
    "de": "der die das und ist nicht ich du ein zu mit den von sie".split(),
    "pt": "o os de que e um uma não para com você uma do da em".split(),
    "it": "il lo che di è non un per con sono una della gli le".split(),
}

_KANA = re.compile(r"[\u3040-\u30ff]")
_HANGUL = re.compile(r"[\uac00-\ud7af]")
_CJK = re.compile(r"[\u4e00-\u9fff]")
_CYRILLIC = re.compile(r"[\u0400-\u04ff]")
_WORD = re.compile(r"[a-záéíóúñüàâçèêëîïôûùœäößãõì]+", re.IGNORECASE)


def language_name(code: str) -> str:
    return LANGUAGES.get(code, code)


def detect_language(texts: Iterable[str], sample_chars: int = 6000) -> Optional[str]:
    """Detecta el idioma de forma aproximada. Devuelve None si no está seguro."""
    sample = ""
    for text in texts:
        sample += text + "\n"
        if len(sample) >= sample_chars:
            break
    letters = [c for c in sample if c.isalpha()]
    if not letters:
        return None
    total = len(letters)

    if len(_KANA.findall(sample)) / total > 0.05:
        return "ja"
    if len(_HANGUL.findall(sample)) / total > 0.2:
        return "ko"
    if len(_CYRILLIC.findall(sample)) / total > 0.2:
        return "ru"
    if len(_CJK.findall(sample)) / total > 0.2:
        return "zh"

    words = [w.lower() for w in _WORD.findall(sample)]
    scores = Counter()
    for code, stops in _STOPWORDS.items():
        stopset = set(stops)
        scores[code] = sum(1 for w in words if w in stopset)
    ranked = scores.most_common(2)
    if not ranked or ranked[0][1] < 2:
        return None
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]
