import unittest
from unittest.mock import patch
import bridge

VILLAGE={"id":"v1","slug":"open-chat","agents":[{"id":"t1","name":"GPT-5.6 Terra"},{"id":"g1","name":"Gemini"}]}
def ev(i, agent, thinking, kind="CONSOLIDATE"):
    return {"eventIndex":i,"createdAt":f"2026-10-23T21:0{i}:00Z",
            "data":{"actionType":kind, "agentId":agent,
                    "output":{"thinking":thinking}}}

class ReasoningDiagnosticTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(bridge.parse("/village diag open-chat 2026-10-23 Terra"),
                         ("diag","open-chat","2026-10-23","Terra"))

    def test_detect_nonlatin_but_ignore_newlines_and_other_agents(self):
        feed={"events":[ev(1,"t1","Hello world.\nJust ordinary reasoning.\n"*10),
                        ev(2,"t1","рҟ" * 180),
                        ev(3,"g1","рҟ" * 200)],"hasMore":False}
        with patch.object(bridge,"call",return_value=feed) as getter:
            output=bridge.reasoning_diagnostic(VILLAGE,"2026-10-23","Terra")
        self.assertIn("reasoning entries: 2",output)
        self.assertIn("anomalous-Unicode entries: 1",output)
        self.assertIn("event 2",output)
        self.assertNotIn("event 3",output)
        self.assertNotIn("event 1 GPT",output)
        self.assertEqual(getter.call_count,1)

    def test_no_reasoning(self):
        feed={"events":[{"eventIndex":2,"createdAt":"2026-10-23T10:00:00Z",
                         "data":{"actionType":"USER_TALK","speakerName":"User","content":"Hello"}}],
              "hasMore":False}
        with patch.object(bridge,"call",return_value=feed):
            self.assertIn("No public thinking records",
                          bridge.reasoning_diagnostic(VILLAGE,"2026-10-23","Terra"))
if __name__ == "__main__":unittest.main()
