import json
import unittest

from app.models import STATUS_NEEDS_REVIEW, STATUS_PENDING, STATUS_REVIEWED, STATUS_TRANSLATED
from app.providers.base import TranslationProvider
from app.services.pipeline import Cancelled, PipelineError
from tests.helpers import TempCase

import threading


class DropPlaceholders(TranslationProvider):
    """Proveedor que pierde las variables: simula un mal motor."""
    name = "drop"

    def is_available(self):
        return True, ""

    def translate_batch(self, texts, s, t):
        return ["traducido" for _ in texts]


class PipelineTests(TempCase):
    def setUp(self):
        super().setUp()
        self.src = self.write("g.json", json.dumps({"a": "ゲームを始める", "b": "こんにちは、{player}さん！",
                                                    "c": "ゲームを始める"}))

    def test_import_detects_language(self):
        project = self.service.import_file(self.src, "demo", "auto", "es")
        self.assertEqual(project.source_lang, "ja")
        self.assertEqual(self.service.stats(project.id), {STATUS_PENDING: 3, "total": 3})

    def test_same_language_rejected(self):
        with self.assertRaises(PipelineError):
            self.service.import_file(self.src, "demo", "ja", "ja")

    def test_full_flow_with_mock(self):
        project = self.service.import_file(self.src, "demo", "auto", "es")
        report = self.service.translate(project.id, "mock")
        self.assertEqual(report["translated"], 3)
        out = self.dir / "out.json"
        self.service.export(project.id, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(data["b"], "(es) こんにちは、{player}さん！")

    def test_translate_only_pending(self):
        project = self.service.import_file(self.src, "demo", "auto", "es")
        self.service.translate(project.id, "mock")
        report = self.service.translate(project.id, "mock")
        self.assertEqual((report["translated"], report["needs_review"]), (0, 0))

    def test_lost_placeholder_goes_to_review(self):
        from app.services import project_service
        project_service.get_provider = lambda name: DropPlaceholders()
        try:
            project = self.service.import_file(self.src, "demo", "auto", "es")
            report = self.service.translate(project.id, "drop")
        finally:
            from app.providers import get_provider
            project_service.get_provider = get_provider
        self.assertEqual(report["needs_review"], 1)
        flagged = [s for s in self.service.segments(project.id) if s.status == STATUS_NEEDS_REVIEW]
        self.assertEqual(flagged[0].key, "/b")
        self.assertEqual(flagged[0].issues[0].code, "placeholder_missing")

    def test_manual_save_and_translation_memory(self):
        project = self.service.import_file(self.src, "demo", "auto", "es")
        self.service.translate(project.id, "mock")
        first = self.service.segments(project.id)[0]
        seg, issues = self.service.save_translation(first.id, "Empezar juego")
        self.assertEqual(seg.status, STATUS_REVIEWED)
        self.assertEqual(issues, [])
        # segmento "c" tiene el mismo texto: al retraducir todo, la memoria lo resuelve sin motor
        report = self.service.translate(project.id, "mock", only_pending=False)
        self.assertEqual(report["tm_hits"], 1)
        c = [s for s in self.service.segments(project.id) if s.key == "/c"][0]
        self.assertEqual(c.target_text, "Empezar juego")
        self.assertEqual(c.status, STATUS_TRANSLATED)

    def test_manual_save_with_error_not_stored(self):
        project = self.service.import_file(self.src, "demo", "auto", "es")
        seg_b = [s for s in self.service.segments(project.id) if s.key == "/b"][0]
        seg, issues = self.service.save_translation(seg_b.id, "Hola")
        self.assertEqual(seg.status, STATUS_NEEDS_REVIEW)
        self.assertIsNone(self.db.tm_lookup("ja", "es", seg_b.source_text))

    def test_glossary_enforced(self):
        src = self.write("e.json", json.dumps({"a": "You need the Blue Gem and the key."}))
        project = self.service.import_file(src, "e", "en", "es")
        self.service.add_term(project.id, "Blue Gem", "Gema Azul")
        self.service.translate(project.id, "mock")
        self.assertIn("Gema Azul", self.service.segments(project.id)[0].target_text)

    def test_cancel(self):
        project = self.service.import_file(self.src, "demo", "auto", "es")
        event = threading.Event()
        event.set()
        with self.assertRaises(Cancelled):
            self.service.translate(project.id, "mock", cancel=event)

    def test_existing_po_translations_imported(self):
        po = self.write("a.po", 'msgid "Open"\nmsgstr "Abrir"\n\nmsgid "Close"\nmsgstr ""\n')
        project = self.service.import_file(po, "po", "en", "es")
        stats = self.service.stats(project.id)
        self.assertEqual(stats[STATUS_TRANSLATED], 1)
        self.assertEqual(stats[STATUS_PENDING], 1)

    def test_empty_file(self):
        empty = self.write("empty.json", "{}")
        with self.assertRaises(PipelineError):
            self.service.import_file(empty, "x", "en", "es")


if __name__ == "__main__":
    unittest.main()
