import unittest
from unittest.mock import patch
import bridge

V = {"id": "v1", "slug": "open-chat", "agents": [
    {"id": "g1", "name": "Gemini 3.8 Flash"}]}

EVENTS = {"events": [
    {"eventIndex": 103, "createdAt": "2026-10-09T10:03:00Z",
     "data": {"actionType": "AGENT_TALK", "speakerId": "g1",
              "content": "Responding to the question."}},
    {"eventIndex": 102, "createdAt": "2026-10-09T10:02:00Z",
     "data": {"actionType": "USER_TALK", "speakerName": "Other",
              "content": "Different person."}},
    {"eventIndex": 101, "createdAt": "2026-10-09T10:01:00Z",
     "data": {"actionType": "USER_TALK", "speakerName": "o3",
              "content": "Original test discussion."}},
    {"eventIndex": 104, "createdAt": "2026-10-09T10:04:00Z",
     "data": {"actionType": "CONSOLIDATE", "agentId": "g1",
              "output": {"thinking": "Internal text."}}}
], "hasMore": False}


class SpeakerLookupTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(bridge.parse("/village usermsgs open-chat 2026-10-09 o3"),
                         ("usermsgs", "open-chat", "2026-10-09", "o3"))
        self.assertEqual(bridge.parse("/village around actual-launch-1 2026-10-09 101"),
                         ("around", "actual-launch-1", "2026-10-09", 101))
        self.assertEqual(bridge.parse("/village usermsgs open-chat 2026-10-09 A Name"),
                         ("usermsgs", "open-chat", "2026-10-09", "A Name"))

    def test_exact_user_not_agent_or_mention(self):
        with patch.object(bridge, "call", return_value=EVENTS) as fetch:
            result=bridge.user_messages(V, "2026-10-09", "O3")
        self.assertIn("Original test discussion.", result)
        self.assertNotIn("Different person.", result)
        self.assertNotIn("Internal text.", result)
        self.assertIn("event 101", result)
        self.assertEqual(fetch.call_count, 1)
        self.assertIn("date=2026-10-09", fetch.call_args.args[0])

    def test_context_sorted_and_bounded(self):
        with patch.object(bridge, "call", return_value=EVENTS):
            result=bridge.around_message(V, "2026-10-09", 101)
        self.assertIn("event 101", result)
        self.assertIn("Gemini 3.8 Flash", result)
        self.assertNotIn("Internal text.", result)
        self.assertLess(result.index("event 101"), result.index("event 102"))
        self.assertLess(result.index("event 102"), result.index("event 103"))

    def test_does_not_post_messages(self):
        with patch.object(bridge, "call", return_value=EVENTS) as fetch:
            bridge.user_messages(V, "2026-10-09", "o3")
        self.assertEqual(len(fetch.call_args.args), 1)
        self.assertNotIn("/api/chat/messages", fetch.call_args.args[0])

if __name__ == "__main__":
    unittest.main()
