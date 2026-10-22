import unittest
from unittest.mock import patch
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
