import sys
import unittest
from unittest import mock

from app.providers import stanza_stub


class StanzaStubTests(unittest.TestCase):
    def test_registers_stub_when_missing_and_fails_clearly(self):
        saved = {n: sys.modules.pop(n, None) for n in ("stanza", "spacy")}
        try:
            with mock.patch.object(stanza_stub.importlib.util, "find_spec", return_value=None):
                self.assertTrue(stanza_stub.install_if_missing())
                self.assertFalse(stanza_stub.install_if_missing())
            stub = sys.modules["stanza"]
            self.assertIn("spacy", sys.modules)
            with self.assertRaises(AttributeError):
                getattr(stub, "Pipeline")
            self.assertFalse(hasattr(stub, "__wrapped__"))   # inspect.unwrap lo consulta
        finally:
            for name, module in saved.items():
                sys.modules.pop(name, None)
                if module is not None:
                    sys.modules[name] = module

    def test_does_nothing_when_stanza_present(self):
        saved = {n: sys.modules.get(n) for n in ("stanza", "spacy")}
        sys.modules["stanza"] = object()
        sys.modules["spacy"] = object()
        try:
            self.assertFalse(stanza_stub.install_if_missing())
        finally:
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main()
