#!/usr/bin/env python3
"""Generate the Apollo theme for RMUX from the bundled palette snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
OUTPUT_PATH = ROOT / "apollo-rmux.conf"
PALETTE_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"


def load_palette() -> dict:
    raw = PALETTE_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PALETTE_SHA256:
        raise ValueError(f"palette snapshot hash mismatch: {digest}")
    palette = json.loads(raw)
    if palette.get("id") != "apollo" or palette.get("schemaVersion") != 1:
        raise ValueError("unsupported Apollo palette snapshot")
    return palette


def resolve_role(palette: dict, role: str) -> str:
    reference = palette["roles"][role]
    if not (reference.startswith("{colors.") and reference.endswith("}")):
        raise ValueError(f"role {role!r} is not a color reference")
    return palette["colors"][reference[8:-1]]


def render(palette: dict) -> str:
    color = lambda role: resolve_role(palette, role)
    surface = palette["colors"]["surface"]
    cyan = palette["colors"]["cyan"]
    magenta = palette["colors"]["magenta"]
    return f'''# Apollo for RMUX
# Generated from palette/apollo.json by scripts/generate.py; do not edit.
# RMUX/tmux-compatible theme options only; no status content, keys, or shell behavior.

set-option -g status-style "bg={color("canvas")},fg={color("textPrimary")}"
set-option -g status-left-style "bg={color("focus")},fg={color("canvas")},bold"
set-option -g status-right-style "bg={color("canvas")},fg={color("textSecondary")}"
set-window-option -g window-status-style "bg={surface},fg={color("textInactive")}"
set-window-option -g window-status-current-style "bg={color("information")},fg={color("canvas")},bold"
set-window-option -g window-status-activity-style "bg={surface},fg={color("error")},bold"
set-window-option -g window-status-bell-style "bg={color("error")},fg={color("canvas")},bold"
set-option -g pane-border-style "fg={color("selection")}"
set-option -g pane-active-border-style "fg={color("focus")}"
set-option -g display-panes-colour "{color("information")}"
set-option -g display-panes-active-colour "{color("focus")}"
set-option -g message-style "bg={color("warning")},fg={color("canvas")},bold"
set-option -g message-command-style "bg={color("information")},fg={color("canvas")},bold"
set-window-option -g mode-style "bg={color("focus")},fg={color("canvas")},bold"
set-window-option -g copy-mode-match-style "bg={cyan},fg={color("canvas")}"
set-window-option -g copy-mode-current-match-style "bg={magenta},fg={color("canvas")},bold"
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if apollo-rmux.conf is stale")
    args = parser.parse_args()
    expected = render(load_palette())
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != expected:
            print(f"{OUTPUT_PATH.relative_to(ROOT)} is not generated from the palette")
            return 1
        print("apollo-rmux.conf is up to date")
        return 0
    OUTPUT_PATH.write_text(expected, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
