import unittest

from app.languages import detect_language


class DetectTests(unittest.TestCase):
    def test_japanese(self):
        self.assertEqual(detect_language(["ゲームを始める", "終了"]), "ja")

    def test_korean(self):
        self.assertEqual(detect_language(["게임을 시작합니다"]), "ko")

    def test_russian(self):
        self.assertEqual(detect_language(["Начать игру"]), "ru")

    def test_chinese(self):
        self.assertEqual(detect_language(["开始游戏", "退出游戏"]), "zh")

    def test_english(self):
        self.assertEqual(detect_language(["You have the key and the map.", "This is what we need."]), "en")

    def test_spanish(self):
        self.assertEqual(detect_language(["Tienes la llave y el mapa.", "Esto es lo que no se puede."]), "es")

    def test_unknown(self):
        self.assertIsNone(detect_language(["123", "!!!"]))


if __name__ == "__main__":
    unittest.main()
