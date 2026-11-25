"""Archivos gettext (.po / .pot), con soporte de formas plurales y actualización de la cabecera.

Una entrada con plural genera dos textos: el singular (clave normal) y el plural (clave «<clave> [plural]»).
Al exportar se escriben tantas formas msgstr[N] como indique el idioma de destino (p. ej. 2 en español, 1 en japonés).
"""
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


PLURAL_SUFFIX = " [plural]"

# idioma -> (nº de formas, expresión de Plural-Forms)
_RU = "n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2"
PLURAL_FORMS = {
    "ja": (1, "0"), "zh": (1, "0"), "ko": (1, "0"), "vi": (1, "0"), "th": (1, "0"), "id": (1, "0"),
    "fr": (2, "n > 1"), "pt": (2, "n > 1"),
    "ru": (3, _RU), "uk": (3, _RU),
    "pl": (3, "n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2"),
    "cs": (3, "(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2"),
    "ga": (5, "n==1 ? 0 : n==2 ? 1 : (n>2 && n<7) ? 2 : (n>6 && n<11) ? 3 : 4"),
}


def plural_info(target_lang: str):
    return PLURAL_FORMS.get(re.split(r"[-_]", (target_lang or "").lower())[0], (2, "n != 1"))


def _new_block():
    return {"head": [], "ctx": None, "id": None, "idp": None, "str": None, "plural": False,
            "field": None, "strlines": [], "tail": [], "strn": {}, "strn_idx": None}


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
            cur["idp"] = _unquote(s[12:])
            cur["field"] = "idp"
            cur["head"].append(line)
        elif s.startswith("msgid"):
            cur["id"] = _unquote(s[5:])
            cur["field"] = "id"
            cur["head"].append(line)
        elif s.startswith("msgstr["):
            cur["plural"] = True
            cur["field"] = "strn"
            close = s.index("]")
            cur["strn_idx"] = int(s[7:close])
            cur["strn"][cur["strn_idx"]] = _unquote(s[close + 1:])
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
                cur["idp"] += _unquote(s)
                cur["head"].append(line)
            elif f == "str":
                cur["str"] += _unquote(s)
                cur["strlines"].append(line)
            elif f == "strn":
                cur["strn"][cur["strn_idx"]] += _unquote(s)
                cur["tail"].append(line)
    if cur:
        blocks.append(cur)
    return blocks


def _key(block) -> str:
    return f"{block['ctx']}|{block['id']}" if block["ctx"] else block["id"]


def _translatable(block) -> bool:
    if not block["id"]:
        return False
    return (block["idp"] is not None and bool(block["strn"])) if block["plural"] else block["str"] is not None


def _plural_lines(singular: str, plural: str, count: int) -> List[str]:
    lines: List[str] = []
    for i in range(count):
        text = singular if i == 0 else plural
        lines.append(f"msgstr[{i}] {_quote(text)}")
    return lines


def _update_header(text: str, target_lang: str) -> str:
    """Pone Language y Plural-Forms del idioma de destino y elimina duplicados de msgcat."""
    count, expr = plural_info(target_lang)
    seen, out = set(), []
    for line in text.split("\n"):
        if line.startswith("#-#-#-#-#"):
            continue
        name = line.split(":", 1)[0] if ":" in line else None
        if name in ("Language", "Plural-Forms"):
            continue
        if name and name in seen:
            continue
        if name:
            seen.add(name)
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    out += [f"Language: {target_lang}", f"Plural-Forms: nplurals={count}; plural={expr};"]
    return "\n".join(out) + "\n"


class PoHandler(FormatHandler):
    name = "gettext PO"
    extensions = (".po", ".pot")

    def parse(self, path) -> List[ParsedEntry]:
        entries: List[ParsedEntry] = []
        for b in _parse_blocks(read_text(path)):
            if not _translatable(b):
                continue
            if b["plural"]:
                entries.append(ParsedEntry(_key(b), b["id"], context=b["ctx"] or "", existing=b["strn"].get(0, "")))
                entries.append(ParsedEntry(_key(b) + PLURAL_SUFFIX, b["idp"], context=b["ctx"] or "",
                                           existing=b["strn"].get(1, "")))
            else:
                entries.append(ParsedEntry(_key(b), b["id"], context=b["ctx"] or "", existing=b["str"] or ""))
        return entries

    def export(self, source_path, output_path, translations: Dict[str, str], target_lang: str) -> None:
        count, _expr = plural_info(target_lang)
        out: List[str] = []
        for block in _parse_blocks(read_text(source_path)):
            head = block["head"]
            if block["id"] == "" and block["str"] is not None:   # cabecera del archivo
                head = [ln for ln in head if ln.strip() not in ("#, fuzzy",)]
                out.extend(head)
                out.extend(_msgstr_lines(_update_header(block["str"], target_lang)))
                out.extend(block["tail"])
                out.append("")
                continue
            out.extend(head)
            key = _key(block)
            if _translatable(block) and block["plural"]:
                sing = translations.get(key, block["strn"].get(0, ""))
                plur = translations.get(key + PLURAL_SUFFIX, block["strn"].get(1, ""))
                out.extend(_plural_lines(sing, plur, count))
            else:
                if _translatable(block) and key in translations:
                    out.extend(_msgstr_lines(translations[key]))
                else:
                    out.extend(block["strlines"])
                out.extend(block["tail"])
            out.append("")
        with open(output_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out))
