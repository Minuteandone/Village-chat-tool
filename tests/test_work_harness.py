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

if __name__=="__main__":
    unittest.main()
