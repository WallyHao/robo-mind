from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_DIR = _PROJECT_ROOT / "src"

_COLOR_INFO = "cyan"
_COLOR_WARN = "yellow"
_COLOR_ERROR = "red"
_COLOR_OK = "green"
_COLOR_LLM = "magenta"
_COLOR_EXEC = "blue"
_COLOR_DONE = "bright_white"
_COLOR_DIM = "dim"

processes: list[subprocess.Popen[bytes]] = []


def _load_dotenv() -> None:
    env_file = _PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=False)


def main() -> None:
    _load_dotenv()
    console.print()
    console.print(
        Panel.fit(
            "[bold bright_white]RoboMind[/bold bright_white] v0.1.0",
            subtitle="[dim]body + brain dual-process architecture[/dim]",
        )
    )

    _check_env()
    _start_body()
    _start_brain()

    while True:
        try:
            time.sleep(0.5)
            _check_alive()
        except KeyboardInterrupt:
            _shutdown()
            break


def _check_env() -> None:
    env_file = _PROJECT_ROOT / ".env"
    if not env_file.exists():
        console.print(
            f"[{_COLOR_WARN}]WARNING: .env file not found at {env_file}[/{_COLOR_WARN}]"
        )
        console.print(f"[{_COLOR_DIM}]  copy .env.example to .env and fill in your API keys[/{_COLOR_DIM}]")
    else:
        console.print(f"[{_COLOR_DIM}]using .env from {env_file}[/{_COLOR_DIM}]")

    dimos_path = os.environ.get("DIMOS_SITE_PATH", "")
    if not dimos_path or not os.path.isdir(dimos_path):
        console.print(
            f"[{_COLOR_ERROR}]ERROR: DIMOS_SITE_PATH not set or path not found[/{_COLOR_ERROR}]"
        )
        console.print(
            f"[{_COLOR_DIM}]  set DIMOS_SITE_PATH in .env to the dimOS site-packages directory[/{_COLOR_DIM}]"
        )
        sys.exit(1)

    console.print(f"[{_COLOR_DIM}]dimOS path: {dimos_path}[/{_COLOR_DIM}]")


def _start_body() -> None:
    console.print(f"[{_COLOR_INFO}]starting body process...[/{_COLOR_INFO}]")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(_SRC_DIR) + ":" + env.get("PYTHONPATH", "")

    p = subprocess.Popen(
        [sys.executable, "-m", "robomind.body"],
        cwd=str(_PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,
    )
    processes.append(p)
    console.print(f"[{_COLOR_DIM}]  body pid={p.pid}[/{_COLOR_DIM}]")

    console.print(f"[{_COLOR_INFO}]waiting for body to signal ready (odom channel)...[/{_COLOR_INFO}]")

    attempts = 0
    max_attempts = 30
    while attempts < max_attempts:
        time.sleep(1)
        attempts += 1
        if p.poll() is not None:
            console.print(
                f"[{_COLOR_ERROR}]ERROR: body process exited with code {p.returncode}[/{_COLOR_ERROR}]"
            )
            if p.stdout:
                tail = p.stdout.read()
                console.print(f"[{_COLOR_DIM}]{tail.decode(errors='replace')[-500:]}[/{_COLOR_DIM}]")
            sys.exit(1)
        console.print(f"[{_COLOR_DIM}]  waiting... ({attempts}/{max_attempts})[/{_COLOR_DIM}]")

    console.print(f"[{_COLOR_OK}]body process running[/{_COLOR_OK}]")


def _start_brain() -> None:
    console.print(f"[{_COLOR_INFO}]starting brain process...[/{_COLOR_INFO}]")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(_SRC_DIR) + ":" + env.get("PYTHONPATH", "")

    p = subprocess.Popen(
        [sys.executable, "-m", "robomind.brain"],
        cwd=str(_PROJECT_ROOT),
        env=env,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
        text=False,
    )
    processes.append(p)
    console.print(f"[{_COLOR_DIM}]  brain pid={p.pid}[/{_COLOR_DIM}]")

    p.wait()

    if p.returncode == 0:
        console.print(f"[{_COLOR_DONE}]brain process exited normally[/{_COLOR_DONE}]")
    else:
        console.print(
            f"[{_COLOR_ERROR}]brain process exited with code {p.returncode}[/{_COLOR_ERROR}]"
        )

    _shutdown()


def _check_alive() -> None:
    for p in processes:
        if p.poll() is not None and p is not processes[-1]:
            console.print(
                f"[{_COLOR_ERROR}]ERROR: subprocess pid={p.pid} died unexpectedly "
                f"(code={p.returncode})[/{_COLOR_ERROR}]"
            )
            _shutdown()
            sys.exit(1)


def _shutdown() -> None:
    console.print(f"[{_COLOR_WARN}]shutting down...[/{_COLOR_WARN}]")
    for p in reversed(processes):
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
    console.print(f"[{_COLOR_DONE}]all processes terminated[/{_COLOR_DONE}]")


if __name__ == "__main__":
    main()
