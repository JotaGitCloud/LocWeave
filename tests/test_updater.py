import unittest

from app import updater


def release(tag, pre=False, draft=False, variant="slim", size=100):
    url = f"https://github.com/JotaGitCloud/LocWeave/releases/download/{tag}/x.exe"
    return {"tag_name": tag, "prerelease": pre, "draft": draft, "body": "notas", "html_url": "https://x/" + tag,
            "assets": [{"name": f"LocWeave-Setup-{variant}.exe", "size": size, "digest": "sha256:ab",
                        "browser_download_url": url}]}


class VersionTests(unittest.TestCase):
    def test_ordering(self):
        order = ["0.1.0-dev", "v0.1.0-alpha1", "0.1.0-beta1", "v0.1.0-beta2", "0.1.0-rc1", "0.1.0", "0.1.1", "0.2.0"]
        keys = [updater.version_key(v) for v in order]
        self.assertEqual(keys, sorted(keys))

    def test_unparseable_is_lowest(self):
        self.assertLess(updater.version_key("???"), updater.version_key("0.0.1-dev"))


class FindUpdateTests(unittest.TestCase):
    def test_newer_release_found(self):
        info = updater.find_update("0.1.0-beta1", [release("v0.1.0-beta1", True), release("v0.1.0-beta2", True)])
        self.assertEqual(info.tag, "v0.1.0-beta2")
        self.assertEqual(info.version, "0.1.0-beta2")
        self.assertEqual(info.sha256, "ab")

    def test_same_or_older_means_no_update(self):
        self.assertIsNone(updater.find_update("0.1.0-beta2", [release("v0.1.0-beta2", True)]))
        self.assertIsNone(updater.find_update("0.2.0", [release("v0.1.0")]))

    def test_final_beats_its_prerelease(self):
        info = updater.find_update("0.1.0-beta2", [release("v0.1.0-beta2", True), release("v0.1.0")])
        self.assertEqual(info.tag, "v0.1.0")

    def test_respects_variant_drafts_and_prereleases(self):
        rels = [release("v0.3.0", variant="full"), release("v0.2.0", draft=True), release("v0.1.5", pre=True)]
        self.assertIsNone(updater.find_update("0.1.0", rels, "slim", include_prereleases=False))
        self.assertEqual(updater.find_update("0.1.0", rels, "full").tag, "v0.3.0")
        self.assertEqual(updater.find_update("0.1.0", rels, "slim").tag, "v0.1.5")

    def test_dev_builds_detected(self):
        self.assertTrue(updater.is_dev("0.1.0-dev"))
        self.assertFalse(updater.is_dev("0.1.0-beta1"))


class DownloadGuardTests(unittest.TestCase):
    def test_rejects_foreign_urls(self):
        info = updater.UpdateInfo("1", "v1", "", "LocWeave-Setup-slim.exe", "https://evil.example/x.exe", 1, "", "")
        with self.assertRaises(updater.UpdateError):
            updater.download_installer(info, __import__("pathlib").Path("/tmp/lw_upd_test"), lambda *a: None)


if __name__ == "__main__":
    unittest.main()
