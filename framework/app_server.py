"""Starts TestMu Lite as a uvicorn subprocess for a test session."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class AppServer:
    """Runs the app with TEST_MODE=1 on a free port and a throwaway database."""

    def __init__(self, db_path: Path, log_path: Path, extra_env: dict[str, str] | None = None):
        self.port = free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.db_path = db_path
        self.log_path = log_path
        self.extra_env = extra_env or {}
        self.process: subprocess.Popen | None = None

    def start(self, timeout_s: float) -> None:
        env = os.environ | {"TEST_MODE": "1", "DB_PATH": str(self.db_path)} | self.extra_env
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log = self.log_path.open("w", encoding="utf-8")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(self.port)],
            env=env, stdout=self._log, stderr=subprocess.STDOUT,
        )
        self._wait_until_up(timeout_s)

    def _wait_until_up(self, timeout_s: float) -> None:
        # Any HTTP answer means the server is up. /health may legitimately be 503 when
        # an environment fault is injected, so the status code is not checked here.
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"App server exited early; see {self.log_path}")
            try:
                httpx.get(f"{self.base_url}/health", timeout=1)
                return
            except httpx.TransportError:
                # Polling a subprocess during fixture setup, not waiting inside a test.
                time.sleep(0.1)
        self.stop()
        raise RuntimeError(f"App server did not start within {timeout_s}s; see {self.log_path}")

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if getattr(self, "_log", None):
            self._log.close()
