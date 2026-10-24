import unittest
from unittest.mock import patch
import bridge

class PublicEventSchemaTests(unittest.TestCase):
    def test_command_parse(self):
        self.assertEqual(bridge.parse("/village inspect open-chat 2026-10-23 2"),
                         ("inspect", "open-chat", "2026-10-23", 2))

    def test_inspection_is_read_only_and_bounded(self):
        v={"id":"v1","slug":"open-chat"}
        data={"events":[{"eventIndex":1,"createdAt":"2026-10-23T10:00:00Z",
                          "data":{"actionType":"AGENT_TALK","speakerId":"a","content":"hello"}},
                         {"eventIndex":2,"createdAt":"2026-10-23T10:01:00Z",
                          "data":{"actionType":"TRACE_EXAMPLE","traceId":"xyz","summary":"hidden"}}],
              "hasMore":True}
        with patch.object(bridge, "call", return_value=data) as spy:
            result=bridge.inspect_event_page(v,"2026-10-23",1)
        self.assertIn("TRACE_EXAMPLE",result)
        self.assertIn("dataKeys",result)
        self.assertNotIn("hello",result)
        self.assertNotIn("hidden",result)
        self.assertEqual(spy.call_count,1)
        self.assertIn("/api/events?",spy.call_args.args[0])
        self.assertEqual(len(spy.call_args.args),1)

    def test_bounds(self):
        with self.assertRaises(ValueError):
            bridge.inspect_event_page({"id":"v1"}, "2026-10-23", 200)

if __name__ == "__main__": unittest.main()
