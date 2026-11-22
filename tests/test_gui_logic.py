import importlib.util
import unittest

HAS_QT = importlib.util.find_spec("PySide6") is not None


@unittest.skipUnless(HAS_QT, "PySide6 no está instalado")
class MiniWeaveTests(unittest.TestCase):
    def test_cells_follow_proportions(self):
        from app.gui.delegates import ProjectDelegate
        cells = ProjectDelegate.mini_weave({"reviewed": 50, "translated": 50, "needs_review": 0, "pending": 0})
        self.assertEqual(len(cells), ProjectDelegate.CELLS * ProjectDelegate.ROWS)
        self.assertEqual(cells.count("reviewed"), cells.count("translated"))
        self.assertNotIn("pending", cells)

    def test_empty_project_is_all_pending(self):
        from app.gui.delegates import ProjectDelegate
        self.assertEqual(set(ProjectDelegate.mini_weave({})), {"pending"})

    def test_layout_is_a_permutation(self):
        from app.gui.delegates import ProjectDelegate
        counts = {"reviewed": 3, "translated": 20, "needs_review": 7, "pending": 22}
        cells = ProjectDelegate.mini_weave(counts)
        self.assertEqual(sorted(cells), sorted(ProjectDelegate.mini_weave(counts)))
        self.assertEqual(len(set(range(len(cells)))), len(cells))


if __name__ == "__main__":
    unittest.main()
