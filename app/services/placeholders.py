"""Protección de variables, etiquetas y términos del glosario antes de traducir.

Los elementos se reemplazan por marcadores (XPH0X, XPH1X…) que los motores suelen respetar, y se
restauran al final. Si un marcador se pierde, la etapa de validación lo detecta.
"""
import re
from collections import Counter
from typing import Dict, List, Tuple

PLACEHOLDER_RE = re.compile("|".join([
    r"\{[^{}\n]*\}",                                          # {nombre} {0} {i} {w=0.5}
    r"%(?:\([^)]+\))?[-+ #0]*\d*(?:\.\d+)?[sdifxXoeEgGcru]",  # printf: %s %d %(x)s
    r"%%",
    r"<[^<>\n]+>",                                            # <b> </b> <color=#fff>
    r"\[[^\[\]\n]+\]",                                        # [jugador] (Ren'Py)
    r"\\[ntr]",                                               # \n \t escritos como texto
    r"\n",                                                    # salto de línea real
    r"\$\{[^}]*\}|\$[A-Za-z_]\w*",                            # ${var} $var
]))


def extract_placeholders(text: str) -> Counter:
    return Counter(PLACEHOLDER_RE.findall(text))


def _is_word(ch: str) -> bool:
    return bool(ch) and ch.isalnum()


def mask(text: str, glossary: Dict[str, str] = None) -> Tuple[str, Dict[str, Tuple[str, bool, bool]]]:
    """Devuelve (texto con marcadores, {marcador: (valor, espacio_izq, espacio_der)}).

    Si el marcador queda pegado a una letra, se le añade un espacio para que el motor lo trate como
    palabra aparte; ese espacio se retira al restaurar.
    """
    mapping: Dict[str, Tuple[str, bool, bool]] = {}

    def new_token(m, value: str) -> str:
        left = _is_word(m.string[m.start() - 1]) if m.start() > 0 else False
        right = _is_word(m.string[m.end()]) if m.end() < len(m.string) else False
        token = f"XPH{len(mapping)}X"
        mapping[token] = (value, left, right)
        return (" " if left else "") + token + (" " if right else "")

    masked = PLACEHOLDER_RE.sub(lambda m: new_token(m, m.group(0)), text)
    for term in sorted((glossary or {}), key=len, reverse=True):
        if not term.strip():
            continue
        pattern = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE)
        masked = pattern.sub(lambda m, t=term: new_token(m, glossary[t]), masked)
    return masked, mapping


_SPACED_TOKEN_RE = re.compile(r"( ?)X\s*PH\s*(\d+)\s*X( ?)", re.IGNORECASE)


def restore(translated: str, mapping: Dict[str, Tuple[str, bool, bool]]) -> Tuple[str, List[str]]:
    """Reemplaza los marcadores. Devuelve (texto, lista de marcadores que no aparecieron)."""
    seen = set()

    def repl(m):
        token = f"XPH{int(m.group(2))}X"
        if token not in mapping:
            return m.group(0)
        seen.add(token)
        value, pad_left, pad_right = mapping[token]
        return ("" if pad_left else m.group(1)) + value + ("" if pad_right else m.group(3))

    text = _SPACED_TOKEN_RE.sub(repl, translated)
    return text, [t for t in mapping if t not in seen]
