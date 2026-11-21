import unittest

from app.services.placeholders import mask, restore
from app.services.validation import has_errors, validate


class PlaceholderTests(unittest.TestCase):
    def test_roundtrip(self):
        text = "Hola {name}, tienes %d <b>monedas</b>\nAdiós [player]"
        masked, mapping = mask(text)
        self.assertNotIn("{name}", masked)
        restored, missing = restore(masked, mapping)
        self.assertEqual(restored, text)
        self.assertEqual(missing, [])

    def test_glossary_applied(self):
        masked, mapping = mask("Toma la espada", {"espada": "sword"})
        restored, _ = restore(masked, mapping)
        self.assertEqual(restored, "Toma la sword")

    def test_tolerates_mangled_tokens(self):
        masked, mapping = mask("Hi {name}!")
        restored, missing = restore(masked.replace("XPH0X", "xph 0 x"), mapping)
        self.assertEqual(restored, "Hi {name}!")
        self.assertEqual(missing, [])

    def test_missing_token_reported(self):
        _, mapping = mask("Hi {name}!")
        _, missing = restore("Hola", mapping)
        self.assertEqual(missing, ["XPH0X"])

    def test_cjk_spacing_removed(self):
        masked, mapping = mask("こんにちは{name}さん")
        self.assertEqual(restore(masked, mapping)[0], "こんにちは{name}さん")


class ValidationTests(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(validate("Hello {name}", "Hola {name}"), [])

    def test_missing_variable(self):
        issues = validate("Hello {name}", "Hola")
        self.assertTrue(has_errors(issues))
        self.assertEqual(issues[0].code, "placeholder_missing")

    def test_extra_variable(self):
        self.assertTrue(has_errors(validate("Hello", "Hola {name}")))

    def test_empty(self):
        self.assertTrue(has_errors(validate("Hello", "  ")))

    def test_newline_warning_is_not_error(self):
        issues = validate("a\nb", "ab")
        self.assertFalse(has_errors([i for i in issues if i.code == "newlines"]))
        self.assertTrue(any(i.code == "newlines" for i in issues))


if __name__ == "__main__":
    unittest.main()
