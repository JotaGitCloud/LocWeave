import sys
import unittest
from unittest import mock

from app.providers import stanza_stub


class StanzaStubTests(unittest.TestCase):
    def test_registers_stub_when_missing_and_fails_clearly(self):
        saved = sys.modules.pop("stanza", None)
        try:
            with mock.patch.object(stanza_stub.importlib.util, "find_spec", return_value=None):
                self.assertTrue(stanza_stub.install_if_missing())
                self.assertFalse(stanza_stub.install_if_missing())
            stub = sys.modules["stanza"]
            with self.assertRaises(ImportError):
                getattr(stub, "Pipeline")
        finally:
            sys.modules.pop("stanza", None)
            if saved is not None:
                sys.modules["stanza"] = saved

    def test_does_nothing_when_stanza_present(self):
        saved = sys.modules.get("stanza")
        sys.modules["stanza"] = object()
        try:
            self.assertFalse(stanza_stub.install_if_missing())
        finally:
            if saved is None:
                sys.modules.pop("stanza", None)
            else:
                sys.modules["stanza"] = saved


if __name__ == "__main__":
    unittest.main()
