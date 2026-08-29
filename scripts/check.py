#!/usr/bin/env python3
"""Validate both generated themes in isolated RMUX-compatible servers."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME_PATHS = {
    "dark": ROOT / "apollo-rmux.conf",
    "light": ROOT / "apollo-rmux-light.conf",
}
RESTRICTED_DARK = "#665c54"
EXPECTED = {
    "dark": {
        "global": {
            "status-style": "bg=#141617,fg=#cfbc97",
            "status-left-style": "bg=#fabd2f,fg=#141617,bold",
            "status-right-style": "bg=#141617,fg=#d5c4a1",
            "pane-border-style": "fg=#3c3836",
            "pane-active-border-style": "fg=#fabd2f",
            "display-panes-colour": "#83a598",
            "display-panes-active-colour": "#fabd2f",
            "message-style": "bg=#fabd2f,fg=#141617,bold",
            "message-command-style": "bg=#83a598,fg=#141617,bold",
        },
        "window": {
            "window-status-style": "bg=#1d2021,fg=#928374",
            "window-status-current-style": "bg=#83a598,fg=#141617,bold",
            "window-status-activity-style": "bg=#1d2021,fg=#fb4934,bold",
            "window-status-bell-style": "bg=#fb4934,fg=#141617,bold",
            "mode-style": "bg=#fabd2f,fg=#141617,bold",
            "copy-mode-match-style": "bg=#8ec07c,fg=#141617",
            "copy-mode-current-match-style": "bg=#d3869b,fg=#141617,bold",
        },
    },
    "light": {
        "global": {
            "status-style": "bg=#f9f5d7,fg=#3c3836",
            "status-left-style": "bg=#8a5200,fg=#f9f5d7,bold",
            "status-right-style": "bg=#f9f5d7,fg=#504945",
            "pane-border-style": "fg=#ebdbb2",
            "pane-active-border-style": "fg=#8a5200",
            "display-panes-colour": "#076678",
            "display-panes-active-colour": "#8a5200",
            "message-style": "bg=#8a5200,fg=#f9f5d7,bold",
            "message-command-style": "bg=#076678,fg=#f9f5d7,bold",
        },
        "window": {
            "window-status-style": "bg=#fbf1c7,fg=#665c54",
            "window-status-current-style": "bg=#076678,fg=#f9f5d7,bold",
            "window-status-activity-style": "bg=#fbf1c7,fg=#9d0006,bold",
            "window-status-bell-style": "bg=#9d0006,fg=#f9f5d7,bold",
            "mode-style": "bg=#8a5200,fg=#f9f5d7,bold",
            "copy-mode-match-style": "bg=#356b4d,fg=#f9f5d7",
            "copy-mode-current-match-style": "bg=#8f3f71,fg=#f9f5d7,bold",
        },
    },
}
ALLOWED_OPTIONS = set(EXPECTED["dark"]["global"]) | set(EXPECTED["dark"]["window"])
OPTION_RE = re.compile(r'^set-(?:window-)?option -g ([a-z-]+) "[^"]+"$')


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True, **kwargs)


def variant_for_path(theme_path: Path) -> str:
    for variant, path in THEME_PATHS.items():
        if theme_path == path:
            return variant
    raise ValueError(f"unknown theme path: {theme_path}")


def validate_theme_only(theme_path: Path = THEME_PATHS["dark"]) -> None:
    text = theme_path.read_text(encoding="utf-8")
    if variant_for_path(theme_path) == "dark" and RESTRICTED_DARK in text.lower():
        raise AssertionError(f"{RESTRICTED_DARK} is restricted to ANSI bright black in Apollo Dark")
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


def validate_isolated_server(binary: str, variant: str = "dark") -> None:
    executable = shutil.which(binary) if Path(binary).name == binary else binary
    if executable is None:
        raise FileNotFoundError(binary)
    theme_path = THEME_PATHS[variant]
    expected = EXPECTED[variant]
    with tempfile.TemporaryDirectory(prefix=f"apollo-rmux-{variant}-"):
        socket = f"/tmp/apollo-rmux-{uuid.uuid4().hex}.sock"
        base = [executable, "-S", socket]
        try:
            run([*base, "-f", "/dev/null", "new-session", "-d", "-s", "apollo"])
            run([*base, "source-file", str(theme_path)])
            for option, wanted in expected["global"].items():
                actual = run([*base, "show-options", "-gv", option]).stdout.strip()
                if actual != wanted:
                    raise AssertionError(f"{variant} {option}: expected {wanted!r}, got {actual!r}")
            for option, wanted in expected["window"].items():
                actual = run([*base, "show-options", "-gwv", option]).stdout.strip()
                if actual != wanted:
                    raise AssertionError(f"{variant} {option}: expected {wanted!r}, got {actual!r}")
        finally:
            subprocess.run([*base, "kill-server"], text=True, capture_output=True, check=False)


def main() -> int:
    run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"])
    for theme_path in THEME_PATHS.values():
        validate_theme_only(theme_path)
    binary = compatible_binary()
    if binary:
        for variant in THEME_PATHS:
            validate_isolated_server(binary, variant)
        print(f"isolated {Path(binary).name} compatibility options are correct for both variants")
    else:
        print("rmux/tmux not installed; native compatibility validation skipped")
    print("RMUX Apollo theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
