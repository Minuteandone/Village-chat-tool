import pathlib
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import work_harness as h

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.work=pathlib.Path(self.temp.name)/"workspace"
        self.work.mkdir()
        self.patcher=patch.object(h,"WORKSPACE",self.work)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def test_write_read_list(self):
        message="/work write notes/example.txt\nHello, tool harness!\nLine two"
        self.assertIn("Wrote",h.execute(message))
        self.assertIn("Hello, tool harness!",h.execute("/work read notes/example.txt"))
        self.assertIn("notes",h.execute("/work list"))
        self.assertIn("example.txt",h.execute("/work list notes"))

    def test_reject_traversal(self):
        for name in ["../secret.py","/etc/passwd","notes/../../secret.py","~/.ssh/id_rsa"]:
            with self.assertRaises(ValueError):
                h.resolve(name,expect_file=True)

    def test_write_needs_newline(self):
        with self.assertRaises(ValueError):
            h.execute("/work write example.py")

    def test_run_is_containerized_offline(self):
        (self.work/"script.py").write_text("print('test')\n")
        fake=MagicMock(returncode=0,stdout="test\n",stderr="")
        with patch.object(h.subprocess,"run",return_value=fake) as run:
            result=h.execute("/work run script.py")
        self.assertIn("test",result)
        args=run.call_args.args[0]
        self.assertIn("--network",args)
        self.assertEqual(args[args.index("--network")+1],"none")
        self.assertIn("--read-only",args)
        self.assertNotIn("sh",args)
        self.assertEqual(args[-2:]," -I -B".split()[0:0]+["-B","script.py"])

    def test_block_non_python(self):
        (self.work/"bad.sh").write_text("echo hi")
        with self.assertRaises(ValueError):
            h.execute("/work run bad.sh")

    def test_fetch_rejects_unsafe_hosts(self):
        for url in ["http://example.com/a","https://localhost/test",
                    "https://127.0.0.1/a","https://evil.example/a",
                    "https://user:pass@gitlab.com/a"]:
            with self.assertRaises(ValueError):
                h.execute("/work fetch "+url+" file.txt")

    def test_fetch_public_bounded(self):
        response=MagicMock()
        response.read.return_value=b"source file"
        op=MagicMock()
        op.open.return_value.__enter__.return_value=response
        with patch.object(h.urllib.request,"build_opener",return_value=op):
            result=h.execute("/work fetch https://raw.githubusercontent.com/user/repo/main/file.txt notes/copy.txt")
        self.assertIn("Fetched",result)
        self.assertEqual((self.work/"notes/copy.txt").read_bytes(),b"source file")


    def test_github_reply_mention_safety(self):
        raw="From @AgentName to @someone: contact help@example.org; literal @\u200bAlreadySafe"
        safe=h.github_safe(raw)
        self.assertIn("@\u200bAgentName",safe)
        self.assertIn("@\u200bsomeone",safe)
        self.assertIn("help@\u200bexample.org",safe)
        self.assertEqual(h.github_safe(safe),safe)

    def test_reject_escape_via_symlink(self):
        outside=pathlib.Path(self.temp.name)/"outside"
        outside.mkdir()
        (outside/"private.txt").write_text("keep out")
        (self.work/"link").symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):
            h.execute("/work read link/private.txt")
        with self.assertRaises(ValueError):
            h.execute("/work write link/evil.txt\nnot allowed")
        self.assertFalse((outside/"evil.txt").exists())

    def test_enforce_write_limit(self):
        with self.assertRaises(ValueError):
            h.execute("/work write large.txt\n"+"X"*(h.MAX_FILE+1))
        self.assertFalse((self.work/"large.txt").exists())

    def test_run_enforces_resource_limits(self):
        (self.work/"script.py").write_text("print('test')\n")
        fake=MagicMock(returncode=0,stdout="done",stderr="")
        with patch.object(h.subprocess,"run",return_value=fake) as run:
            h.execute("/work run script.py")
        argv=run.call_args.args[0]
        for flag in ("--network","--read-only","--pids-limit",
                     "--memory","--cpus","--security-opt","--user"):
            self.assertIn(flag,argv)
        self.assertEqual(argv[argv.index("--network")+1],"none")
        self.assertEqual(run.call_args.kwargs["timeout"],45)

    def test_runner_timeout_is_bounded(self):
        (self.work/"slow.py").write_text("while True: pass\n")
        with patch.object(h.subprocess,"run",side_effect=h.subprocess.TimeoutExpired("docker",45)):
            result=h.execute("/work run slow.py")
        self.assertIn("45-second",result)

    def test_oversized_fetch_is_rejected_without_write(self):
        response=MagicMock()
        response.read.return_value=b"x"*(h.MAX_FILE+1)
        opener=MagicMock()
        opener.open.return_value.__enter__.return_value=response
        with patch.object(h.urllib.request,"build_opener",return_value=opener):
            with self.assertRaises(ValueError):
                h.execute("/work fetch https://raw.githubusercontent.com/owner/repo/main/large.dat downloads/large.dat")
        self.assertFalse((self.work/"downloads/large.dat").exists())

    def test_fetch_disables_redirects(self):
        response=MagicMock()
        response.read.return_value=b"ok"
        opener=MagicMock()
        opener.open.return_value.__enter__.return_value=response
        with patch.object(h.urllib.request,"build_opener",return_value=opener) as builder:
            h.execute("/work fetch https://raw.githubusercontent.com/owner/repo/main/a.txt a.txt")
        handler=builder.call_args.args[0]()
        self.assertIsNone(handler.redirect_request(None,None,302,"Moved",{}, "https://evil.example/"))

    def test_unauthorized_issue_comment_does_not_execute(self):
        import json, os
        event={"issue":{"user":{"login":"Minuteandone"}},
               "comment":{"user":{"login":"stranger"},"body":"/work run script.py"}}
        fixture=pathlib.Path(self.temp.name)/"event.json"
        fixture.write_text(json.dumps(event))
        with patch.dict(os.environ,{"GITHUB_EVENT_PATH":str(fixture),
                                   "GITHUB_REPOSITORY":"Minuteandone/Village-chat-tool"}):
            with patch.object(h,"execute") as execute:
                h.main()
                execute.assert_not_called()


if __name__=="__main__":
    unittest.main()
