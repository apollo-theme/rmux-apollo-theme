#!/usr/bin/env python3
"""Generate both Apollo RMUX variants from bundled palette snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {
    "dark": {
        "palette": ROOT / "palette" / "apollo.json",
        "output": ROOT / "apollo-rmux.conf",
        "sha256": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
        "id": "apollo",
    },
    "light": {
        "palette": ROOT / "palette" / "apollo-light.json",
        "output": ROOT / "apollo-rmux-light.conf",
        "sha256": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        "id": "apollo-light",
    },
}


def load_palette(variant: str = "dark") -> dict:
    config = VARIANTS[variant]
    raw = config["palette"].read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != config["sha256"]:
        raise ValueError(f"{variant} palette snapshot hash mismatch: {digest}")
    palette = json.loads(raw)
    if palette.get("id") != config["id"] or palette.get("schemaVersion") != 1:
        raise ValueError(f"unsupported Apollo {variant} palette snapshot")
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
    light = palette["id"] == "apollo-light"
    name = "Apollo Light" if light else "Apollo"
    palette_file = "apollo-light.json" if light else "apollo.json"
    return f'''# {name} for RMUX
# Generated from palette/{palette_file} by scripts/generate.py; do not edit.
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


def render_outputs() -> dict[Path, str]:
    return {
        config["output"]: render(load_palette(variant))
        for variant, config in VARIANTS.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if either RMUX theme is stale")
    args = parser.parse_args()
    expected = render_outputs()
    if args.check:
        stale = [
            path.relative_to(ROOT)
            for path, text in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != text
        ]
        if stale:
            print("stale generated file(s): " + ", ".join(map(str, stale)))
            return 1
        print("RMUX theme variants are up to date")
        return 0
    for path, text in expected.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
