# json_logger — Structured JSON Logger

Lightweight structured JSON logger for AI agents. Zero external dependencies.

## Usage

```python
from json_logger import Logger, Level

log = Logger(name="myapp", level=Level.DEBUG)
log.info("starting", version="1.0")
log.error("failed", code=500, detail="timeout")

# Context manager for persistent fields
with log.context(request_id="abc-123"):
    log.info("processing")  # includes request_id in every entry
```

## Output Format

Each log entry is a single JSON line:
```json
{"ts": "2026-03-27T01:00:00+00:00", "level": "INFO", "logger": "myapp", "msg": "starting", "extra": {"version": "1.0"}}
```

## Output Options

```python
Logger(output=sys.stdout)         # stdout (default)
Logger(output=open("app.log", "w"))  # file
Logger(output=my_callback)        # callable(line: str)
```

## Demo

```bash
python json_logger.py
```

## Tests

```bash
python -m unittest test_json_logger -v
```
