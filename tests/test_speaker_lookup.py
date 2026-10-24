import unittest
from unittest.mock import patch
import bridge

V = {"id": "v1", "slug": "open-chat",
     "agents": [{"id": "a1", "name": "GPT-6 Rook"},
                {"id": "a2", "name": "Gemini 3.1 Pro"}]}
EVENTS = {"events": [
    {"eventIndex": 4, "createdAt": "2026-10-23T09:04:00Z",
     "data": {"actionType": "AGENT_TALK", "speakerId": "a1", "content": "Rook's latest update"}},
    {"eventIndex": 2, "createdAt": "2026-10-23T09:02:00Z",
     "data": {"actionType": "AGENT_TALK", "speakerId": "a2", "content": "Rook was here"}},
    {"eventIndex": 3, "createdAt": "2026-10-23T09:03:00Z",
     "data": {"actionType": "USER_TALK", "speakerName": "Other", "content": "Mention Rook"}},
    {"eventIndex": 1, "createdAt": "2026-10-23T09:01:00Z",
     "data": {"actionType": "USER_TALK", "speakerName": "Rook", "content": "Visitor named Rook"}},
], "hasMore": False}

class SpeakerMessagesTests(unittest.TestCase):
    def test_parser(self):
        self.assertEqual(bridge.parse("/village speaker open-chat recent Rook"),
                         ("speaker", "open-chat", "recent", "Rook"))
        self.assertEqual(bridge.parse("/village speaker actual-launch-1 2026-10-23 GPT-6 Rook"),
                         ("speaker", "actual-launch-1", "2026-10-23", "GPT-6 Rook"))

    def test_agent_and_exact_named_user(self):
        with patch.object(bridge, "call", return_value=EVENTS):
            result=bridge.speaker_messages(V, "2026-10-23", "Rook")
        self.assertIn("Rook's latest update", result)
        self.assertIn("Visitor named Rook", result)
        self.assertNotIn("Rook was here", result)
        self.assertNotIn("Mention Rook", result)
        self.assertLess(result.index("event 1"), result.index("event 4"))

    def test_ambiguous_names(self):
        v={"id":"v1","slug":"open-chat",
           "agents":[{"id":"a1","name":"A Rook"},{"id":"a2","name":"B Rook"}]}
        self.assertIn("Ambiguous", bridge.speaker_messages(v,"2026-10-23","Rook"))

    def test_no_post(self):
        with patch.object(bridge, "call", return_value=EVENTS) as read:
            bridge.speaker_messages(V, "2026-10-23", "Rook")
        self.assertIn("/api/events?", read.call_args.args[0])
        self.assertNotIn("/api/chat/messages", str(read.call_args_list))

if __name__ == "__main__":
    unittest.main()
