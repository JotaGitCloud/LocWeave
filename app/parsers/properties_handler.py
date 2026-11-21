"""Archivos .properties (clave=valor)."""
import re
from typing import Dict, List

from .base import FormatHandler, ParsedEntry, has_letters, read_text

_KV = re.compile(r"^\s*([^\s=:#!][^=:]*?)\s*[=:]\s*(.*)$")


def _unescape(v: str) -> str:
    v = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), v)
    return re.sub(r"\\([ntr\\])", lambda m: {"n": "\n", "t": "\t", "r": "\r", "\\": "\\"}[m.group(1)], v)


def _escape(v: str) -> str:
    return v.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


def _items(text: str):
    """Devuelve ('raw', línea) o ('kv', clave, valor_crudo)."""
    lines = text.splitlines()
    i, items = 0, []
    while i < len(lines):
        line = lines[i]
        m = _KV.match(line)
        if line.strip().startswith(("#", "!")) or not line.strip() or not m:
            items.append(("raw", line))
            i += 1
            continue
        key, value = m.group(1), m.group(2)
        while value.endswith("\\") and (len(value) - len(value.rstrip("\\"))) % 2 == 1 and i + 1 < len(lines):
            i += 1
            value = value[:-1] + lines[i].lstrip()
        items.append(("kv", key, value))
        i += 1
    return items


class PropertiesHandler(FormatHandler):
    name = "Java .properties"
    extensions = (".properties",)

    def parse(self, path) -> List[ParsedEntry]:
        return [ParsedEntry(it[1], _unescape(it[2]), context=it[1])
                for it in _items(read_text(path)) if it[0] == "kv" and has_letters(it[2])]

    def export(self, source_path, output_path, translations: Dict[str, str], target_lang: str) -> None:
        out = []
        for it in _items(read_text(source_path)):
            if it[0] == "raw":
                out.append(it[1])
            elif it[1] in translations:
                out.append(f"{it[1]}={_escape(translations[it[1]])}")
            else:
                out.append(f"{it[1]}={it[2]}")
        with open(output_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out) + "\n")
