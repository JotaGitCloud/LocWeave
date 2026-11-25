import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.services.project_service import LocWeaveService


class TempCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.db = Database(self.dir / "test.db")
        self.service = LocWeaveService(self.db)

    def tearDown(self):
        self.db.close()
        self._tmp.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.dir / name
        path.write_text(content, encoding="utf-8")
        return path
