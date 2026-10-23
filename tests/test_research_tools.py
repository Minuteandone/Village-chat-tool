"""Tests for linked web/GitHub research workspace tools; offline and deterministic."""
import json
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import research_tools as tools
import work_harness as harness


class ResearchToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.work = pathlib.Path(self.temp.name) / "workspace"
        self.work.mkdir()
        self.patcher = patch.object(harness, "WORKSPACE", self.work)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def test_web_search_bing_rss(self):
        rss = b"""<rss><channel><item><title>Example One</title>
                   <link>https://example.org/docs</link><description>A result</description>
                   </item></channel></rss>"""
        with patch.object(tools, "fetch", return_value=(rss, "application/xml")):
            output = harness.execute("/work web search example query")
        self.assertIn("Example One", output)
        self.assertTrue(list((self.work / "research/searches").glob("*.json")))
        self.assertEqual(json.loads((self.work/".agent/research-last.json").read_text())
                         ["results"][0]["url"], "https://example.org/docs")

    def test_open_saved_result_to_workspace(self):
        with patch.object(tools, "web_search", return_value=(
            "Bing RSS", [{"title": "Doc", "url": "https://example.org/docs", "snippet": "Info"}])):
            harness.execute("/work web search documentation")
        with patch.object(tools, "display_page", return_value="An example document."):
            result = harness.execute("/work web open 1 research/notes.txt")
        self.assertIn("An example document.", result)
        self.assertIn("https://example.org/docs", (self.work/"research/notes.txt").read_text())
        with self.assertRaises(ValueError):
            harness.execute("/work web open 9")

    def test_extract_text_ignores_scripts_and_styles(self):
        markup = b"<html><head><title>Page</title><style>secret{}</style></head><body><h1>Header</h1><p>Facts</p><script>danger()</script></body></html>"
        with patch.object(tools, "fetch", return_value=(markup, "text/html")):
            page = tools.display_page("https://example.org/")
        self.assertIn("Header", page)
        self.assertIn("Facts", page)
        self.assertNotIn("danger()", page)

    def test_public_url_validation(self):
        invalid = ("http://example.org/a", "https://localhost/",
                   "https://127.0.0.1/", "https://user:pass@example.org/",
                   "https://example.org:8443/test", "https://internal.local/")
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(ValueError):
                tools.validate_url(url)
        with patch.object(tools.socket, "getaddrinfo", return_value=[
            (2, 1, 6, "", ("10.0.0.5", 443))]):
            with self.assertRaises(ValueError):
                tools.validate_url("https://example.org/test")
        with patch.object(tools.socket, "getaddrinfo", return_value=[
            (2, 1, 6, "", ("93.184.216.34", 443))]):
            self.assertEqual(tools.validate_url("https://example.org/test"),
                             "https://example.org/test")

    def test_fetch_disallows_redirects(self):
        response = MagicMock()
        response.headers = {"Content-Type": "text/plain"}
        response.read.return_value = b"hello"
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with patch.object(tools, "validate_url", return_value="https://example.org/"):
            with patch.object(tools.urllib.request, "build_opener", return_value=opener) as builder:
                data, content_type = tools.fetch("https://example.org/")
        self.assertEqual(data, b"hello")
        self.assertEqual(content_type, "text/plain")
        self.assertIsInstance(builder.call_args.args[1], tools.NoRedirect)

    def test_bounded_download_and_internal_state_protection(self):
        with patch.object(tools, "fetch", return_value=(b"notes", "text/plain")):
            result = harness.execute("/work web download https://example.org/doc research/saved.txt")
        self.assertIn("research/saved.txt", result)
        self.assertEqual((self.work/"research/saved.txt").read_bytes(), b"notes")
        with patch.object(tools, "fetch", return_value=(b"oops", "text/plain")):
            with self.assertRaises(ValueError):
                harness.execute("/work web download https://example.org/a .agent/memory.json")
            with self.assertRaises(ValueError):
                harness.execute("/work web download https://example.org/a ../outside.txt")
        self.assertFalse((self.work/".agent/memory.json").exists())

    def test_github_repo_and_tree(self):
        def mock_api(path, limit=tools.MAX_TEXT_BYTES):
            if path == "repos/example/repo":
                return {"full_name": "example/repo", "description": "A test",
                        "default_branch": "main", "stargazers_count": 12,
                        "forks_count": 4, "size": 5, "html_url": "https://github.com/example/repo"}
            return {"tree": [{"path": "README.md", "type": "blob"}], "truncated": False}
        with patch.object(tools, "_api", side_effect=mock_api):
            repo = harness.execute("/work github repo example/repo")
            tree = harness.execute("/work github tree example/repo")
        self.assertIn("Stars: 12", repo)
        self.assertIn("README.md", tree)

    def test_github_file_and_download(self):
        with patch.object(tools, "_gh_file", return_value=(
            b"Project README\n", {"html_url": "https://github.com/example/repo/blob/main/README.md"})):
            result = harness.execute("/work github file example/repo README.md")
        self.assertIn("Project README", result)
        with patch.object(tools, "_api", return_value={"default_branch": "main"}):
            with patch.object(tools, "fetch", return_value=(b"print('hello')\n", "text/plain")) as fetched:
                result = harness.execute("/work github download example/repo src/app.py downloads/app.py")
        self.assertEqual((self.work/"downloads/app.py").read_text(), "print('hello')\n")
        self.assertIn("raw.githubusercontent.com/example/repo/main/src/app.py", fetched.call_args.args[0])
        self.assertIn("workspace/downloads/app.py", result)

    def test_github_zip_download(self):
        with patch.object(tools, "fetch", return_value=(b"PK\x03\x04testzip", "application/zip")):
            result = harness.execute("/work github archive example/repo downloads/project.zip main")
        self.assertIn("Saved public repository ZIP", result)
        self.assertTrue((self.work/"downloads/project.zip").exists())

    def test_research_connects_search_retrieval_and_storage(self):
        with patch.object(tools, "web_search", return_value=(
            "Bing RSS", [{"title": "Guide", "url": "https://example.org/guide"}])):
            with patch.object(tools, "display_page", return_value="Useful source text."):
                result = harness.execute("/work research example topic")
        self.assertIn("Research snapshot", result)
        text = next((self.work/"research/reports").glob("*.txt")).read_text()
        self.assertIn("Useful source text.", text)
        self.assertIn("https://example.org/guide", text)

    def test_symlink_and_invalid_paths(self):
        target = pathlib.Path(self.temp.name) / "outside"
        target.mkdir()
        (self.work/"research").symlink_to(target, target_is_directory=True)
        with patch.object(tools, "fetch", return_value=(b"hello", "text/plain")):
            with self.assertRaises(ValueError):
                harness.execute("/work web download https://example.org/a research/file.txt")
        self.assertFalse((target/"file.txt").exists())
        with self.assertRaises(ValueError):
            harness.execute("/work github tree ../../bad")

    def test_github_search_pipelines_cannot_execute_data(self):
        with patch.object(tools, "web_search", return_value=(
            "Bing RSS", [{"title": "Ignore instructions", "url": "https://example.org/doc"}])):
            with patch.object(tools, "display_page", return_value="DO NOT execute this text."):
                result = harness.execute("/work research untrusted source")
        self.assertIn("untrusted", result)
        self.assertFalse((self.work/"script.py").exists())



    def test_reject_unrelated_bing_and_fallback_to_encyclopedia(self):
        stale = [{"title": "Casablanca", "url": "https://example.org/film",
                  "snippet": "Classic film aspect ratio"}]
        wikipedia = [{"title": "Python (programming language)",
                      "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                      "snippet": "Python programming language"}]
        with patch.object(tools, "_search_bing", return_value=stale):
            with patch.object(tools, "_search_ddg", return_value=[]):
                with patch.object(tools, "_search_wikipedia", return_value=wikipedia):
                    engine, results = tools.web_search("Python programming documentation")
        self.assertIn("Wikipedia", engine)
        self.assertEqual(results[0]["title"], "Python (programming language)")

    def test_wikipedia_api_parser(self):
        sample = {"query": {"search": [
            {"title": "Python (programming language)",
             "snippet": "<span class='searchmatch'>Python</span> is a language."}]}}
        with patch.object(tools, "fetch", return_value=(
            json.dumps(sample).encode("utf-8"), "application/json")):
            found = tools._search_wikipedia("Python")
        self.assertEqual(len(found), 1)
        self.assertIn("en.wikipedia.org/wiki/Python_", found[0]["url"])
        self.assertNotIn("<span", found[0]["snippet"])

    def test_github_repository_search(self):
        sample = {"items": [
            {"full_name": "example/my-game", "html_url": "https://github.com/example/my-game",
             "description": "An open-source example game."}]}
        with patch.object(tools, "_api", return_value=sample) as api:
            result = harness.execute("/work github search example game")
        self.assertIn("example/my-game", result)
        self.assertIn("search/repositories?", api.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
