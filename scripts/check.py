#!/usr/bin/env python3
"""Validate generated content in an isolated RMUX or compatible tmux server."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME_PATH = ROOT / "apollo-rmux.conf"
RESTRICTED = "#665c54"
EXPECTED_GLOBAL = {
    "status-style": "bg=#141617,fg=#cfbc97",
    "status-left-style": "bg=#fabd2f,fg=#141617,bold",
    "status-right-style": "bg=#141617,fg=#d5c4a1",
    "pane-border-style": "fg=#3c3836",
    "pane-active-border-style": "fg=#fabd2f",
    "display-panes-colour": "#83a598",
    "display-panes-active-colour": "#fabd2f",
    "message-style": "bg=#fabd2f,fg=#141617,bold",
    "message-command-style": "bg=#83a598,fg=#141617,bold",
}
EXPECTED_WINDOW = {
    "window-status-style": "bg=#1d2021,fg=#928374",
    "window-status-current-style": "bg=#83a598,fg=#141617,bold",
    "window-status-activity-style": "bg=#1d2021,fg=#fb4934,bold",
    "window-status-bell-style": "bg=#fb4934,fg=#141617,bold",
    "mode-style": "bg=#fabd2f,fg=#141617,bold",
    "copy-mode-match-style": "bg=#8ec07c,fg=#141617",
    "copy-mode-current-match-style": "bg=#d3869b,fg=#141617,bold",
}
ALLOWED_OPTIONS = set(EXPECTED_GLOBAL) | set(EXPECTED_WINDOW)
OPTION_RE = re.compile(r'^set-(?:window-)?option -g ([a-z-]+) "[^"]+"$')


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True, **kwargs)


def validate_theme_only() -> None:
    text = THEME_PATH.read_text(encoding="utf-8")
    if RESTRICTED in text.lower():
        raise AssertionError(f"{RESTRICTED} is restricted to ANSI bright black")
    seen: set[str] = set()
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        match = OPTION_RE.fullmatch(line)
        if not match:
            raise AssertionError(f"non-theme or malformed command: {line}")
        option = match.group(1)
        if option not in ALLOWED_OPTIONS:
            raise AssertionError(f"unexpected RMUX option: {option}")
        seen.add(option)
    if seen != ALLOWED_OPTIONS:
        raise AssertionError(f"theme option mismatch: missing={sorted(ALLOWED_OPTIONS - seen)}")


def compatible_binary() -> str | None:
    return shutil.which("rmux") or shutil.which("tmux")


def validate_isolated_server(binary: str) -> None:
    executable = shutil.which(binary) if Path(binary).name == binary else binary
    if executable is None:
        raise FileNotFoundError(binary)
    with tempfile.TemporaryDirectory(prefix="apollo-rmux-"):
        socket = f"/tmp/apollo-rmux-{uuid.uuid4().hex}.sock"
        base = [executable, "-S", socket]
        try:
            run([*base, "-f", "/dev/null", "new-session", "-d", "-s", "apollo"])
            run([*base, "source-file", str(THEME_PATH)])
            for option, expected in EXPECTED_GLOBAL.items():
                actual = run([*base, "show-options", "-gv", option]).stdout.strip()
                if actual != expected:
                    raise AssertionError(f"{option}: expected {expected!r}, got {actual!r}")
            for option, expected in EXPECTED_WINDOW.items():
                actual = run([*base, "show-options", "-gwv", option]).stdout.strip()
                if actual != expected:
                    raise AssertionError(f"{option}: expected {expected!r}, got {actual!r}")
        finally:
            subprocess.run([*base, "kill-server"], text=True, capture_output=True, check=False)


def main() -> int:
    run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"])
    validate_theme_only()
    binary = compatible_binary()
    if binary:
        validate_isolated_server(binary)
        print(f"isolated {Path(binary).name} compatibility options are correct")
    else:
        print("rmux/tmux not installed; native compatibility validation skipped")
    print("RMUX Apollo theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
