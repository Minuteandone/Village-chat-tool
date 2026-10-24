"""Read-only public Village date search tests."""
import unittest
from unittest.mock import patch
import bridge

VILLAGE = {
    "id": "v1", "slug": "open-chat",
    "agents": [{"id": "a1", "name": "Gemini 3.1 Pro"}],
    "chatRooms": [{"id": "r1", "name": "general"}],
}

class HistorySearchTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(bridge.parse("/village find open-chat 2026-10-22 help|distress"),
                         ("find", "open-chat", "2026-10-22", "help|distress"))

    def test_date_validation(self):
        with self.assertRaisesRegex(ValueError, "Date"):
            bridge.find(VILLAGE, "2026-02-30", "safety")

    def test_bounded_search(self):
        def get(url, *args, **kwargs):
            if url.endswith("active-dates"):
                return {"dates": ["2026-10-22"]}
            if "/api/events?" in url:
                return {"events": [
                    {"eventIndex": 1, "createdAt": "2026-10-22T12:00:00Z",
                     "data": {"actionType": "USER_TALK", "content": "Sine waves are ordinary maths.",
                              "roomId": "r1", "speakerName": "Human"}},
                    {"eventIndex": 2, "createdAt": "2026-10-22T12:00:03Z",
                     "data": {"actionType": "AGENT_TALK", "content": "Please seek support if distressed.",
                              "roomId": "r1", "speakerId": "a1"}}
                ], "hasMore": False}
            raise AssertionError(url)
        with patch.object(bridge, "call", side_effect=get) as calls:
            reply = bridge.find(VILLAGE, "2026-10-22", "distress|support")
        self.assertIn("1 matching messages", reply)
        self.assertIn("Gemini 3.1 Pro", reply)
        self.assertIn("Sine waves", reply)
        self.assertEqual(calls.call_count, 2)
        self.assertNotIn("/api/chat/messages", str(calls.call_args_list))

    def test_missing_date(self):
        with patch.object(bridge, "call", return_value={"dates": ["2026-10-21"]}):
            reply = bridge.find(VILLAGE, "2026-10-22", "distress")
        self.assertIn("No events available", reply)

if __name__ == "__main__":
    unittest.main()
