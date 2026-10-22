import unittest
import json
import io
from unittest.mock import patch, mock_open
import bridge

VILLAGE = {
    "id": "village-1",
    "chatRooms": [{"id": "room-1", "name": "general"}],
    "agents": [],
}

class BridgeTests(unittest.TestCase):
    def test_read_command(self):
        self.assertEqual(bridge.parse("/village read 7 general"), ("read", 7, "general"))

    def test_post_command(self):
        self.assertEqual(bridge.parse("/village post general hello world"),
                         ("post", "general", "hello world"))

    def test_status_command(self):
        self.assertEqual(bridge.parse("/village status"), ("status",))

    def test_rejects_large_read(self):
        with self.assertRaises(ValueError):
            bridge.parse("/village read 50 all")

    def test_github_safe_mentions_and_idempotence(self):
        raw = "@DeepSeek and @Gemini 3.1 Pro, plus user@example.com"
        safe = bridge.github_safe(raw)
        self.assertNotIn("@DeepSeek", safe)
        self.assertNotIn("@Gemini", safe)
        self.assertNotIn("@example", safe)
        self.assertIn("@\u200bDeepSeek", safe)
        self.assertEqual(bridge.github_safe(safe), safe)

    def test_restore_mentions_only_for_village(self):
        text = "[[at]]DeepSeek, @\u200bGemini and @\u200dArgon"
        self.assertEqual(bridge.village_text(text),
                         "@DeepSeek, @Gemini and @Argon")

    def test_safe_outgoing_command_preserves_village_mentions(self):
        env = {"VILLAGE_VISITOR_ID": "random-visitor-identifier-long-enough",
               "VILLAGE_DISPLAY_NAME": "Starpettergpt"}
        with patch.dict("os.environ", env, clear=True):
            with patch.object(bridge, "call", side_effect=[
                {"id": "visitor-id-1"}, {}, {"hasBeenApproved": True}
            ]) as request:
                bridge.post(VILLAGE, "general", "[[at]]Gemini says hi to @\u200bDeepSeek")
        payload = request.call_args_list[2].args[1]
        self.assertEqual(payload["content"], "@Gemini says hi to @DeepSeek")

    def test_github_issue_reply_neutralizes_export_mentions(self):
        event = {"issue": {"number": 1, "user": {"login": "Minuteandone"}},
                 "comment": {"user": {"login": "Minuteandone"},
                             "body": "/village read 5 general"}}
        env = {"GITHUB_EVENT_PATH": "event.json",
               "GITHUB_REPOSITORY": "Minuteandone/Village-chat-tool",
               "GITHUB_TOKEN": "test"}
        with patch.dict("os.environ", env, clear=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(event))):
                with patch.object(bridge, "get_village", return_value=VILLAGE):
                    with patch.object(bridge, "read",
                                      return_value="**@Gemini**\n> @DeepSeek ping") as reader:
                        with patch.object(bridge, "call") as gh:
                            bridge.main()
        posted_body = gh.call_args.args[1]["body"]
        self.assertEqual(posted_body, "**@\u200bGemini**\n> @\u200bDeepSeek ping")
        reader.assert_called_once()

    def test_large_event_page_is_not_cut_off_at_three_mb(self):
        payload = json.dumps({"events": [], "padding": "x" * 3_001_000}).encode()
        with patch("bridge.urllib.request.urlopen", return_value=io.BytesIO(payload)):
            result = bridge.call("https://theaidigest.org/village/api/events?page=1")
        self.assertEqual(len(result["padding"]), 3_001_000)

    def test_non_event_page_has_bounded_json_size(self):
        payload = json.dumps({"data": "x" * 3_001_000}).encode()
        with patch("bridge.urllib.request.urlopen", return_value=io.BytesIO(payload)):
            with self.assertRaisesRegex(RuntimeError, "safe read limit"):
                bridge.call("https://theaidigest.org/village/api/villages")

    def test_requires_persistent_visitor_id(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(bridge, "call") as request:
                response = bridge.post(VILLAGE, "general", "hi")
        self.assertIn("No message sent", response)
        request.assert_not_called()

    def test_posts_only_through_browser_guest_api(self):
        env = {"VILLAGE_VISITOR_ID": "random-visitor-identifier-long-enough",
               "VILLAGE_DISPLAY_NAME": "ChatGPT GitHub"}
        with patch.dict("os.environ", env, clear=True):
            with patch.object(bridge, "call", side_effect=[
                {"id": "visitor-id-1"}, {}, {"hasBeenApproved": False}
            ]) as request:
                response = bridge.post(VILLAGE, "general", "hello world")
        self.assertIn("Approval pending", response)
        self.assertEqual(request.call_count, 3)
        args = request.call_args_list
        self.assertEqual(args[0].args[0], bridge.BASE + "/api/users")
        self.assertEqual(args[0].args[1]["localStorageId"], env["VILLAGE_VISITOR_ID"])
        self.assertEqual(args[1].args[0], bridge.BASE + "/api/users/display-name")
        self.assertEqual(args[1].kwargs["method"], "PUT")
        self.assertEqual(args[1].args[1]["name"], "ChatGPT GitHub")
        self.assertEqual(args[2].args[0], bridge.BASE + "/api/chat/messages")
        self.assertEqual(args[2].args[1]["userSpeakerId"], "visitor-id-1")
        self.assertEqual(args[2].args[1]["content"], "hello world")

    def test_does_not_post_for_invalid_room(self):
        with patch.dict("os.environ", {"VILLAGE_VISITOR_ID": "some-persistent-random-visitor-key"}, clear=True):
            with patch.object(bridge, "call") as request:
                with self.assertRaises(ValueError):
                    bridge.post(VILLAGE, "unknown", "test")
        request.assert_not_called()

    def test_stops_when_identity_request_fails(self):
        with patch.dict("os.environ", {"VILLAGE_VISITOR_ID": "some-persistent-random-visitor-key"}, clear=True):
            with patch.object(bridge, "call", return_value={}) as request:
                with self.assertRaises(RuntimeError):
                    bridge.post(VILLAGE, "general", "test")
        self.assertEqual(request.call_count, 1)

if __name__ == "__main__":
    unittest.main()
