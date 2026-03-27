#!/usr/bin/env python3
"""Lightweight structured JSON logger for AI agents. Stdlib only."""

import json
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import IntEnum
from io import TextIOBase
from typing import Any, Callable, Dict, Optional, TextIO


class Level(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40


class Logger:
    """Structured JSON logger with levels, context, and configurable output."""

    def __init__(
        self,
        name: str = "root",
        level: Level = Level.INFO,
        output: Optional[Any] = None,
    ):
        self.name = name
        self.level = level
        self._lock = threading.Lock()
        self._context_fields: Dict[str, Any] = {}
        self._output = output or sys.stdout

    def _write(self, entry: dict) -> None:
        line = json.dumps(entry, default=str)
        with self._lock:
            if callable(self._output) and not isinstance(self._output, TextIOBase):
                self._output(line)
            elif hasattr(self._output, "write"):
                self._output.write(line + "\n")
                self._output.flush()

    def _log(self, level: Level, msg: str, **extra: Any) -> None:
        if level < self.level:
            return
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level.name,
            "logger": self.name,
            "msg": msg,
        }
        if self._context_fields:
            entry["extra"] = {**self._context_fields, **extra}
        elif extra:
            entry["extra"] = extra
        self._write(entry)

    def debug(self, msg: str, **extra: Any) -> None:
        self._log(Level.DEBUG, msg, **extra)

    def info(self, msg: str, **extra: Any) -> None:
        self._log(Level.INFO, msg, **extra)

    def warn(self, msg: str, **extra: Any) -> None:
        self._log(Level.WARN, msg, **extra)

    def error(self, msg: str, **extra: Any) -> None:
        self._log(Level.ERROR, msg, **extra)

    @contextmanager
    def context(self, **fields: Any):
        """Add persistent fields to all log entries within this context."""
        old = self._context_fields.copy()
        self._context_fields.update(fields)
        try:
            yield self
        finally:
            self._context_fields = old


if __name__ == "__main__":
    log = Logger(name="demo", level=Level.DEBUG)
    log.debug("starting up", version="1.0")
    log.info("processing request", endpoint="/api/tasks")
    with log.context(request_id="abc-123", user="habie"):
        log.info("inside context")
        log.warn("something fishy", detail="unexpected null")
    log.error("something broke", code=500)
    print("\n--- Demo complete ---")
