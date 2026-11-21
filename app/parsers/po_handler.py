"""Archivos gettext (.po / .pot). Se omiten las entradas con plural."""
import re
from typing import Dict, List

from .base import FormatHandler, ParsedEntry, read_text

_ESC = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return re.sub(r"\\(.)", lambda m: _ESC.get(m.group(1), m.group(1)), s)


def _quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t").replace("\r", "\\r") \
        .replace("\n", "\\n") + '"'


def _msgstr_lines(text: str) -> List[str]:
    if "\n" not in text:
        return [f"msgstr {_quote(text)}"]
    parts = text.split("\n")
    lines = ['msgstr ""']
    for i, part in enumerate(parts):
        piece = part + ("\n" if i < len(parts) - 1 else "")
        if piece:
            lines.append(_quote(piece))
    return lines


def _new_block():
    return {"head": [], "ctx": None, "id": None, "str": None, "plural": False,
            "field": None, "strlines": [], "tail": []}


def _parse_blocks(text: str):
    blocks, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if cur:
                blocks.append(cur)
                cur = None
            continue
        if cur is not None and cur["str"] is not None and s.startswith("#"):
            blocks.append(cur)
            cur = None
        if cur is None:
            cur = _new_block()
        if s.startswith("#"):
            cur["head"].append(line)
        elif s.startswith("msgctxt"):
            cur["ctx"] = _unquote(s[7:])
            cur["field"] = "ctx"
            cur["head"].append(line)
        elif s.startswith("msgid_plural"):
            cur["plural"] = True
            cur["field"] = "idp"
            cur["head"].append(line)
        elif s.startswith("msgid"):
            cur["id"] = _unquote(s[5:])
            cur["field"] = "id"
            cur["head"].append(line)
        elif s.startswith("msgstr["):
            cur["plural"] = True
            cur["field"] = "strn"
            cur["tail"].append(line)
        elif s.startswith("msgstr"):
            cur["str"] = _unquote(s[6:])
            cur["field"] = "str"
            cur["strlines"].append(line)
        elif s.startswith('"'):
            f = cur["field"]
            if f == "ctx":
                cur["ctx"] += _unquote(s)
                cur["head"].append(line)
            elif f == "id":
                cur["id"] += _unquote(s)
                cur["head"].append(line)
            elif f == "idp":
                cur["head"].append(line)
            elif f == "str":
                cur["str"] += _unquote(s)
                cur["strlines"].append(line)
            elif f == "strn":
                cur["tail"].append(line)
    if cur:
        blocks.append(cur)
    return blocks


def _key(block) -> str:
    return f"{block['ctx']}|{block['id']}" if block["ctx"] else block["id"]


def _translatable(block) -> bool:
    return bool(block["id"]) and not block["plural"] and block["str"] is not None


class PoHandler(FormatHandler):
    name = "gettext PO"
    extensions = (".po", ".pot")

    def parse(self, path) -> List[ParsedEntry]:
        return [ParsedEntry(_key(b), b["id"], context=b["ctx"] or "", existing=b["str"] or "")
                for b in _parse_blocks(read_text(path)) if _translatable(b)]

    def export(self, source_path, output_path, translations: Dict[str, str], target_lang: str) -> None:
        out: List[str] = []
        for block in _parse_blocks(read_text(source_path)):
            out.extend(block["head"])
            if _translatable(block) and _key(block) in translations:
                out.extend(_msgstr_lines(translations[_key(block)]))
            else:
                out.extend(block["strlines"])
            out.extend(block["tail"])
            out.append("")
        with open(output_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out))
