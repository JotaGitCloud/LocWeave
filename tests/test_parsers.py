import json
import unittest

from app.parsers import FormatError, get_handler
from tests.helpers import TempCase


class JsonTests(TempCase):
    def test_roundtrip_nested(self):
        src = self.write("a.json", json.dumps({"a": {"b": "Hello"}, "l": ["One", "Two"], "n": 5, "k/x": "Slash"}))
        entries = get_handler(src).parse(src)
        self.assertEqual({e.key for e in entries}, {"/a/b", "/l/0", "/l/1", "/k~1x"})
        out = self.dir / "out.json"
        get_handler(src).export(src, out, {"/a/b": "Hola", "/l/1": "Dos", "/k~1x": "Barra"}, "es")
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(data["a"]["b"], "Hola")
        self.assertEqual(data["l"], ["One", "Dos"])
        self.assertEqual(data["n"], 5)
        self.assertEqual(data["k/x"], "Barra")

    def test_invalid(self):
        src = self.write("bad.json", "{oops")
        with self.assertRaises(FormatError):
            get_handler(src).parse(src)


class CsvTests(TempCase):
    def test_adds_target_column(self):
        src = self.write("a.csv", "key,en\nGREET,Hello\nBYE,Goodbye\nNUM,123\n")
        h = get_handler(src)
        self.assertEqual([e.key for e in h.parse(src)], ["GREET", "BYE"])
        out = self.dir / "out.csv"
        h.export(src, out, {"GREET": "Hola", "BYE": "Adiós"}, "es")
        lines = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "key,en,es")
        self.assertEqual(lines[1], "GREET,Hello,Hola")
        self.assertEqual(lines[3], "NUM,123,")

    def test_semicolon_and_commas_in_text(self):
        src = self.write("b.csv", 'id;text\nA;"Hello, world"\n')
        h = get_handler(src)
        self.assertEqual(h.parse(src)[0].text, "Hello, world")


class PoTests(TempCase):
    PO = ('# comentario\nmsgid ""\nmsgstr ""\n"Language: en\\n"\n\n'
          '#: x.c:1\nmsgid "Hello"\nmsgstr ""\n\n'
          'msgctxt "menu"\nmsgid "Open"\nmsgstr "Abrir"\n\n'
          'msgid "Line1\\nLine2"\nmsgstr ""\n\n'
          'msgid "One apple"\nmsgid_plural "%d apples"\nmsgstr[0] ""\nmsgstr[1] ""\n')

    def test_parse_and_export(self):
        src = self.write("a.po", self.PO)
        h = get_handler(src)
        entries = h.parse(src)
        self.assertEqual([e.key for e in entries], ["Hello", "menu|Open", "Line1\nLine2"])
        self.assertEqual(entries[1].existing, "Abrir")
        out = self.dir / "out.po"
        h.export(src, out, {"Hello": "Hola", "Line1\nLine2": "Uno\nDos"}, "es")
        text = out.read_text(encoding="utf-8")
        self.assertIn('msgstr "Hola"', text)
        self.assertIn('msgstr "Abrir"', text)
        self.assertIn('"Uno\\n"\n"Dos"', text)
        self.assertIn('msgstr[1] ""', text)
        self.assertIn('"Language: en\\n"', text)
        # el archivo exportado se puede volver a leer
        again = h.parse(out)
        self.assertEqual(again[0].existing, "Hola")
        self.assertEqual(again[2].existing, "Uno\nDos")


class PropertiesTests(TempCase):
    def test_roundtrip(self):
        src = self.write("a.properties", "# c\ngreet=Hello {0}\nquit : Quit\nnum=42\n\nmulti=Hello \\\n   world\n")
        h = get_handler(src)
        entries = {e.key: e.text for e in h.parse(src)}
        self.assertEqual(entries, {"greet": "Hello {0}", "quit": "Quit", "multi": "Hello world"})
        out = self.dir / "out.properties"
        h.export(src, out, {"greet": "Hola {0}", "quit": "Salir"}, "es")
        text = out.read_text(encoding="utf-8")
        self.assertIn("# c", text)
        self.assertIn("greet=Hola {0}", text)
        self.assertIn("quit=Salir", text)
        self.assertIn("num=42", text)


class RenpyTests(TempCase):
    RPY = ('define e = Character("Eileen")\nlabel start:\n    scene bg room\n    play music "theme.ogg"\n'
           '    e "Hello, [player]!"\n    "Narration here."\n    e happy "How are you?" with dissolve\n'
           '    menu:\n        "Go left":\n            jump left\n        "Go right" if key:\n            jump right\n'
           '    $ x = _("Inventory")\n    textbutton "Start" action Start()\n')

    def test_extraction(self):
        src = self.write("a.rpy", self.RPY)
        texts = [e.text for e in get_handler(src).parse(src)]
        self.assertEqual(texts, ["Hello, [player]!", "Narration here.", "How are you?", "Go left",
                                 "Go right", "Inventory", "Start"])

    def test_export_only_replaces_strings(self):
        src = self.write("a.rpy", self.RPY)
        h = get_handler(src)
        tr = {e.key: f"T{i}" for i, e in enumerate(h.parse(src))}
        out = self.dir / "out.rpy"
        h.export(src, out, tr, "es")
        text = out.read_text(encoding="utf-8")
        self.assertIn('e "T0"', text)
        self.assertIn('e happy "T2" with dissolve', text)
        self.assertIn('"T4" if key:', text)
        self.assertIn('_("T5")', text)
        self.assertIn('play music "theme.ogg"', text)
        self.assertIn('Character("Eileen")', text)

    def test_quotes_escaped(self):
        src = self.write("a.rpy", 'e "Hi"\n')
        h = get_handler(src)
        out = self.dir / "o.rpy"
        h.export(src, out, {"L1:0": 'Dijo "hola"'}, "es")
        self.assertIn('e "Dijo \\"hola\\""', out.read_text(encoding="utf-8"))


class RegistryTests(TempCase):
    def test_unsupported(self):
        with self.assertRaises(FormatError):
            get_handler("x.xyz")


if __name__ == "__main__":
    unittest.main()
