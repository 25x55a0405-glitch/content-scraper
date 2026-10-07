"""A local stand-in for the Anthropic Messages API, for tests.

It speaks real HTTP, so the official SDK is exercised end to end: request
building, retries on 529/500, error mapping and response parsing. Responses
are scripted per test; every request body is recorded.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def message(text: str, stop_reason: str = "end_turn", model: str = "claude-opus-5-5",
            thinking: bool = True) -> tuple[int, dict]:
    content = ([{"type": "thinking", "thinking": "", "signature": "sig"}] if thinking else []) + \
        [{"type": "text", "text": text}]
    return 200, {"id": "msg_test", "type": "message", "role": "assistant", "model": model,
                 "content": content, "stop_reason": stop_reason, "stop_sequence": None,
                 "usage": {"input_tokens": 1200, "output_tokens": 450}}


def error(status: int, kind: str, msg: str) -> tuple[int, dict]:
    return status, {"type": "error", "error": {"type": kind, "message": msg}}


class FakeAnthropic:
    def __init__(self):
        self.script: list[tuple[int, dict]] = []
        self.requests: list[dict] = []
        self.headers: list[dict] = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("content-length", 0)))
                fake.requests.append(json.loads(body or b"{}"))
                fake.headers.append(dict(self.headers))
                status, payload = fake.script.pop(0) if fake.script else error(500, "api_error", "no script")
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                if status in (429, 529, 500):
                    self.send_header("retry-after", "0")
                self.end_headers()
                self.wfile.write(data)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
