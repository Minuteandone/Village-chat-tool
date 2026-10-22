"""Offline checks for public GitLab read-only bridge."""
import unittest
from unittest.mock import patch
import gitlab_reader
import bridge

PROJECT = {"path_with_namespace":"ai-village-agents/village/example",
           "web_url":"https://gitlab.com/ai-village-agents/village/example",
           "visibility":"public","default_branch":"main","description":"Test"}

class GitLabTests(unittest.TestCase):
    def test_parse_gitlab_command(self):
        self.assertEqual(bridge.parse("/village gitlab example file docs/README.md"),
                         ("gitlab","example","file docs/README.md"))

    def test_project_scope(self):
        self.assertEqual(gitlab_reader.project_name("example"),
                         "ai-village-agents/village/example")
        self.assertEqual(gitlab_reader.project_name("open-chat/paperdoll"),
                         "ai-village-agents/open-chat/paperdoll")
        self.assertEqual(gitlab_reader.project_name("ai-village-agents/open-chat/paperdoll"),
                         "ai-village-agents/open-chat/paperdoll")
        with self.assertRaises(ValueError):
            gitlab_reader.project_name("someone-else/secret")
        with self.assertRaises(ValueError):
            gitlab_reader.project_name("../secret")

    def test_summary_public_read(self):
        with patch.object(gitlab_reader,"get",return_value=PROJECT) as method:
            result=gitlab_reader.run("example","summary")
        self.assertIn("public",result)
        self.assertEqual(method.call_count,1)
        self.assertIn("%2F",method.call_args.args[0])

    def test_read_file_only_get(self):
        with patch.object(gitlab_reader,"get",side_effect=[PROJECT, "Hello!"]) as method:
            result=gitlab_reader.run("example","file README.md")
        self.assertIn("Hello!",result)
        self.assertEqual(method.call_count,2)
        self.assertEqual(method.call_args.kwargs["raw"],True)

    def test_merge_request_details(self):
        obj={"title":"Review candidate", "state":"opened","iid":7,"description":"Details"}
        with patch.object(gitlab_reader,"get",side_effect=[PROJECT,obj]) as method:
            result=gitlab_reader.run("example","mr 7")
        self.assertIn("Review candidate",result)
        self.assertEqual(method.call_count,2)

    def test_block_directory_traversal(self):
        with patch.object(gitlab_reader,"get",return_value=PROJECT) as method:
            with self.assertRaises(ValueError):
                gitlab_reader.run("example","file ../README")
        self.assertEqual(method.call_count,1)

    def test_invalid_commands(self):
        with patch.object(gitlab_reader,"get",return_value=PROJECT):
            with self.assertRaises(ValueError):
                gitlab_reader.run("example","publish something")

if __name__=="__main__":
    unittest.main()
