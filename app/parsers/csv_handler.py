"""CSV con columna de clave (opcional) y columna de texto. La traducción va en una columna nueva."""
import csv
import io
from typing import Dict, List, Optional, Tuple

from .base import FormatError, FormatHandler, ParsedEntry, has_letters, read_text

KEY_NAMES = {"key", "id", "clave", "identifier", "name"}
TEXT_NAMES = {"text", "source", "original", "texto", "string", "value", "dialogue", "en", "es", "ja",
              "zh", "ko", "fr", "de", "pt", "it", "ru"}


class CsvHandler(FormatHandler):
    name = "CSV"
    extensions = (".csv",)

    def _read(self, path):
        text = read_text(path)
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(io.StringIO(text, newline=""), dialect))
        if len(rows) < 2:
            raise FormatError("El CSV necesita una fila de encabezado y al menos una fila de datos.")
        return rows, dialect

    @staticmethod
    def _columns(header: List[str]) -> Tuple[Optional[int], int]:
        lowered = [h.strip().lower() for h in header]
        key_col = next((i for i, h in enumerate(lowered) if h in KEY_NAMES), None)
        text_col = next((i for i, h in enumerate(lowered) if h in TEXT_NAMES and i != key_col), None)
        if text_col is None:
            text_col = next((i for i in range(len(header)) if i != key_col), 0)
        return key_col, text_col

    @staticmethod
    def _keys(rows, key_col) -> List[str]:
        keys, seen = [], {}
        for n, row in enumerate(rows[1:], start=2):
            base = row[key_col].strip() if key_col is not None and key_col < len(row) and row[key_col].strip() \
                else f"row{n}"
            seen[base] = seen.get(base, 0) + 1
            keys.append(base if seen[base] == 1 else f"{base}#{seen[base]}")
        return keys

    def parse(self, path) -> List[ParsedEntry]:
        rows, _ = self._read(path)
        key_col, text_col = self._columns(rows[0])
        keys = self._keys(rows, key_col)
        out = []
        for key, row in zip(keys, rows[1:]):
            if text_col < len(row) and has_letters(row[text_col]):
                out.append(ParsedEntry(key, row[text_col]))
        return out

    def export(self, source_path, output_path, translations: Dict[str, str], target_lang: str) -> None:
        rows, dialect = self._read(source_path)
        header = rows[0]
        key_col, _ = self._columns(header)
        keys = self._keys(rows, key_col)
        if target_lang in [h.strip() for h in header]:
            col = [h.strip() for h in header].index(target_lang)
        else:
            header.append(target_lang)
            col = len(header) - 1
        for key, row in zip(keys, rows[1:]):
            while len(row) <= col:
                row.append("")
            if key in translations:
                row[col] = translations[key]
        with open(output_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, dialect=dialect, lineterminator="\n")
            writer.writerows(rows)
