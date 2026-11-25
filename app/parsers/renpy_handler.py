"""Scripts de Ren'Py (.rpy): diálogos, opciones de menú, _("...") y text/textbutton.

Es una extracción básica por líneas: no interpreta bloques python ni cadenas de varias líneas.
"""
import re
from typing import Dict, List, Tuple

from .base import FormatHandler, ParsedEntry, has_letters, read_text

_SKIP_WORDS = {
    "define", "default", "image", "play", "queue", "stop", "show", "scene", "hide", "jump", "call",
    "return", "label", "python", "init", "renpy", "transform", "voice", "window", "pause", "with",
    "if", "elif", "else", "while", "screen", "style", "translate", "import", "from", "pass", "for",
    "key", "action", "add", "use", "id", "tooltip", "background", "style_prefix", "sensitive",
}
_STR = r'"((?:\\.|[^"\\])*)"'
_DIALOGUE = re.compile(r'^(\s*)((?:[A-Za-z_]\w*\s+){0,3}?)' + _STR + r'(\s+with\s+\w+)?\s*$')
_MENU = re.compile(r'^(\s*)' + _STR + r'(\s+if\s+.+)?\s*:\s*$')
_TEXTUI = re.compile(r'^(\s*(?:text|textbutton)\s+)' + _STR)
_UNDERSCORE = re.compile(r'_\(\s*"((?:\\.|[^"\\])*)"\s*\)')


def _spans(line: str) -> List[Tuple[int, int, str]]:
    """Posiciones (inicio, fin, texto) del contenido de las cadenas traducibles de la línea."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return []
    found = [(m.start(1), m.end(1), m.group(1)) for m in _UNDERSCORE.finditer(line)]
    if found:
        return found
    m = _TEXTUI.match(line)
    if m:
        return [(m.start(2), m.end(2), m.group(2))]
    m = _MENU.match(line)
    if m:
        return [(m.start(2), m.end(2), m.group(2))]
    m = _DIALOGUE.match(line)
    if m:
        words = m.group(2).split()
        if words and words[0] in _SKIP_WORDS:
            return []
        return [(m.start(3), m.end(3), m.group(3))]
    return []


class RenpyHandler(FormatHandler):
    name = "Ren'Py"
    extensions = (".rpy",)

    def parse(self, path) -> List[ParsedEntry]:
        out = []
        for n, line in enumerate(read_text(path).splitlines(), start=1):
            for idx, (_, _, text) in enumerate(_spans(line)):
                if has_letters(text):
                    out.append(ParsedEntry(f"L{n}:{idx}", text, context=f"línea {n}"))
        return out

    def export(self, source_path, output_path, translations: Dict[str, str], target_lang: str) -> None:
        lines = read_text(source_path).splitlines()
        for n, line in enumerate(lines, start=1):
            spans = _spans(line)
            for idx in reversed(range(len(spans))):
                key = f"L{n}:{idx}"
                if key in translations:
                    start, end, _ = spans[idx]
                    safe = translations[key].replace("\n", "\\n")
                    safe = re.sub(r'(?<!\\)"', '\\"', safe)
                    line = line[:start] + safe + line[end:]
            lines[n - 1] = line
        with open(output_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
