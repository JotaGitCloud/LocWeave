import sys
import unittest
from unittest import mock

from app.providers import stanza_stub


class StanzaStubTests(unittest.TestCase):
    def test_registers_stub_when_missing_and_fails_clearly(self):
        with mock.patch.dict(sys.modules, clear=False):
            sys.modules.pop("stanza", None)
            with mock.patch("importlib.util.find_spec", return_value=None):
                self.assertTrue(stanza_stub.install_if_missing())
            import stanza
            with self.assertRaises(ImportError):
                stanza.Pipeline
            self.assertFalse(stanza_stub.install_if_missing())
            sys.modules.pop("stanza", None)


if __name__ == "__main__":
    unittest.main()
