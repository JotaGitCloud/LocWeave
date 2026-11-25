"""JSON (plano o anidado). Las claves se identifican con rutas tipo JSON Pointer."""
import json
from typing import Dict, List

from .base import FormatError, FormatHandler, ParsedEntry, has_letters, read_text


def _enc(part) -> str:
    return str(part).replace("~", "~0").replace("/", "~1")


def _dec(part: str) -> str:
    return part.replace("~1", "/").replace("~0", "~")


class JsonHandler(FormatHandler):
    name = "JSON"
    extensions = (".json",)

    def _load(self, path):
        try:
            return json.loads(read_text(path))
        except ValueError as exc:
            raise FormatError(f"JSON inválido: {exc}") from exc

    def parse(self, path) -> List[ParsedEntry]:
        out: List[ParsedEntry] = []

        def walk(node, parts):
            if isinstance(node, str):
                if has_letters(node):
                    out.append(ParsedEntry("/" + "/".join(_enc(p) for p in parts), node,
                                           context=str(parts[-1]) if parts else ""))
            elif isinstance(node, dict):
                for k, v in node.items():
                    walk(v, parts + [k])
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, parts + [i])

        walk(self._load(path), [])
        return out

    def export(self, source_path, output_path, translations: Dict[str, str], target_lang: str) -> None:
        data = self._load(source_path)
        for key, text in translations.items():
            parts = [_dec(p) for p in key.lstrip("/").split("/")]
            node = data
            try:
                for p in parts[:-1]:
                    node = node[int(p)] if isinstance(node, list) else node[p]
                last = parts[-1]
                if isinstance(node, list):
                    node[int(last)] = text
                else:
                    node[last] = text
            except (KeyError, IndexError, ValueError, TypeError):
                continue
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
