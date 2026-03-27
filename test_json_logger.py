"""Tests for json_logger.py"""

import json
import os
import tempfile
import threading
import unittest
from io import StringIO

from json_logger import Level, Logger


class TestLogger(unittest.TestCase):
    def _make_logger(self, **kwargs):
        buf = StringIO()
        kwargs.setdefault("output", buf)
        kwargs.setdefault("level", Level.DEBUG)
        return Logger(**kwargs), buf

    def _parse(self, buf):
        lines = buf.getvalue().strip().split("\n")
        return [json.loads(l) for l in lines if l]

    def test_info_level(self):
        log, buf = self._make_logger()
        log.info("hello")
        entries = self._parse(buf)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["level"], "INFO")
        self.assertEqual(entries[0]["msg"], "hello")

    def test_all_levels(self):
        log, buf = self._make_logger()
        log.debug("d")
        log.info("i")
        log.warn("w")
        log.error("e")
        entries = self._parse(buf)
        self.assertEqual([e["level"] for e in entries], ["DEBUG", "INFO", "WARN", "ERROR"])

    def test_level_filtering(self):
        log, buf = self._make_logger(level=Level.WARN)
        log.debug("skip")
        log.info("skip")
        log.warn("keep")
        log.error("keep")
        entries = self._parse(buf)
        self.assertEqual(len(entries), 2)

    def test_extra_fields(self):
        log, buf = self._make_logger()
        log.info("test", foo="bar", count=42)
        entry = self._parse(buf)[0]
        self.assertEqual(entry["extra"]["foo"], "bar")
        self.assertEqual(entry["extra"]["count"], 42)

    def test_context_manager(self):
        log, buf = self._make_logger()
        with log.context(request_id="abc"):
            log.info("inside")
        log.info("outside")
        entries = self._parse(buf)
        self.assertEqual(entries[0]["extra"]["request_id"], "abc")
        self.assertNotIn("extra", entries[1])

    def test_context_merge(self):
        log, buf = self._make_logger()
        with log.context(a="1"):
            log.info("test", b="2")
        entry = self._parse(buf)[0]
        self.assertEqual(entry["extra"]["a"], "1")
        self.assertEqual(entry["extra"]["b"], "2")

    def test_nested_context(self):
        log, buf = self._make_logger()
        with log.context(a="1"):
            with log.context(b="2"):
                log.info("nested")
            log.info("outer")
        entries = self._parse(buf)
        self.assertIn("a", entries[0]["extra"])
        self.assertIn("b", entries[0]["extra"])
        self.assertIn("a", entries[1]["extra"])
        self.assertNotIn("b", entries[1]["extra"])

    def test_timestamp_format(self):
        log, buf = self._make_logger()
        log.info("ts")
        entry = self._parse(buf)[0]
        self.assertIn("T", entry["ts"])
        self.assertIn("+", entry["ts"])

    def test_callback_output(self):
        lines = []
        log = Logger(level=Level.DEBUG, output=lines.append)
        log.info("callback")
        self.assertEqual(len(lines), 1)
        self.assertIn("callback", lines[0])

    def test_file_output(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            path = f.name
            log = Logger(level=Level.DEBUG, output=f)
            log.info("to file")
        with open(path) as f:
            entry = json.loads(f.read().strip())
        self.assertEqual(entry["msg"], "to file")
        os.unlink(path)

    def test_thread_safety(self):
        log, buf = self._make_logger()
        def write_many():
            for i in range(100):
                log.info(f"msg-{i}")
        threads = [threading.Thread(target=write_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        entries = self._parse(buf)
        self.assertEqual(len(entries), 400)

    def test_json_serializable(self):
        log, buf = self._make_logger()
        log.info("test")
        line = buf.getvalue().strip()
        json.loads(line)  # should not raise

    def test_logger_name(self):
        log, buf = self._make_logger(name="myapp")
        log.info("test")
        entry = self._parse(buf)[0]
        self.assertEqual(entry["logger"], "myapp")


if __name__ == "__main__":
    unittest.main()
