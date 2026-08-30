#!/usr/bin/env python3
"""Validate both generated themes in isolated RMUX-compatible servers."""

from __future__ import annotations

import re
import shutil
import subprocess
from html.parser import HTMLParser
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
README_CONTRACT_MARKERS = {
    "dark source command": 'rmux source-file "$HOME/.config/rmux-apollo-theme/apollo-rmux.conf"',
    "light source command": 'rmux source-file "$HOME/.config/rmux-apollo-theme/apollo-rmux-light.conf"',
    "dark status output": "bg=#141617,fg=#cfbc97",
    "light status output": "bg=#f9f5d7,fg=#3c3836",
}
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


def _blockquote_body(line: str) -> tuple[int, str]:
    """Return blockquote depth and content after standard quote markers."""
    depth = 0
    while match := re.match(r" {0,3}> ?", line):
        depth += 1
        line = line[match.end():]
    return depth, line


def _list_item_body(line: str) -> tuple[int | None, str]:
    """Return list continuation indentation and content after a list marker."""
    match = re.match(r"( {0,3}(?:[-+*]|\d{1,9}[.)]))([ \t]+)", line)
    if match is None:
        return None, line
    whitespace = match.group(2)
    prefix = match.group(1) + whitespace[0]
    return len(prefix.expandtabs(4)), line[len(prefix):]


def _strip_indent(line: str, width: int) -> str | None:
    """Strip at least width columns of spaces or tabs from one line."""
    columns = 0
    index = 0
    while index < len(line) and columns < width and line[index] in " \t":
        columns += 1 if line[index] == " " else 4 - (columns % 4)
        index += 1
    return line[index:] if columns >= width else None


def _strip_indented_code(text: str) -> str:
    """Remove indented code after optional standard blockquote markers."""
    visible: list[str] = []
    for line in text.splitlines(keepends=True):
        body = _blockquote_body(line)[1]
        _, list_body = _list_item_body(body)
        if _strip_indent(list_body, 4) is None:
            visible.append(line)
    return "".join(visible)


def _strip_fenced_code(text: str) -> str:
    """Remove completed CommonMark-style fenced blocks without hiding unmatched text."""
    lines = text.splitlines(keepends=True)
    visible: list[str] = []
    index = 0
    while index < len(lines):
        quote_depth, body = _blockquote_body(lines[index].rstrip("\r\n"))
        list_indent, body = _list_item_body(body)
        opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})([^\r\n]*)", body)
        if not opening or (opening.group(1)[0] == "`" and "`" in opening.group(2)):
            visible.append(lines[index])
            index += 1
            continue
        fence = opening.group(1)
        closer = re.compile(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*")
        closing_index = next(
            (
                candidate
                for candidate in range(index + 1, len(lines))
                if (
                    (quoted := _blockquote_body(lines[candidate].rstrip("\r\n")))[0] == quote_depth
                    and (
                        (candidate_body := (
                            _strip_indent(quoted[1], list_indent)
                            if list_indent is not None
                            else quoted[1]
                        ))
                        is not None
                    )
                    and closer.fullmatch(candidate_body)
                )
            ),
            None,
        )
        if closing_index is None:
            visible.extend(lines[index:])
            break
        index = closing_index + 1
    return "".join(visible)


def _strip_inline_code(text: str) -> str:
    """Remove code spans with isolated opening and exact matching backtick runs."""
    parts: list[str] = []
    index = 0
    while opening := re.search(r"(?<![\\`])(`+)(?!`)", text[index:]):
        start = index + opening.start()
        run = opening.group(1)
        closer = re.search(rf"(?<![\\`]){re.escape(run)}(?!`)", text[start + len(run):])
        if closer is None:
            parts.append(text[index:])
            return "".join(parts)
        parts.append(text[index:start])
        index = start + len(run) + closer.end()
    parts.append(text[index:])
    return "".join(parts)


class _VisibleHTMLCollector(HTMLParser):
    """Collect text from HTML elements that are visible to readers."""

    SUPPRESSED = {"code", "pre", "script", "style", "template"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    HIDDEN_STYLE = re.compile(
        r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)\s*(?:!\s*important\s*)?(?=;|$)",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []
        self.suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.VOID:
            return
        suppressed = tag in self.SUPPRESSED or any(
            name == "hidden"
            or (name == "aria-hidden" and (value or "").casefold() == "true")
            or (name == "style" and bool(self.HIDDEN_STYLE.search(value or "")))
            for name, value in attrs
        )
        self.stack.append((tag, suppressed))
        self.suppressed_depth += int(suppressed)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        pass

    def handle_endtag(self, tag: str) -> None:
        match = next((index for index in range(len(self.stack) - 1, -1, -1) if self.stack[index][0] == tag), None)
        if match is None:
            return
        closed = self.stack[match:]
        del self.stack[match:]
        self.suppressed_depth -= sum(suppressed for _, suppressed in closed)

    def handle_data(self, data: str) -> None:
        if not self.suppressed_depth:
            self.parts.append(data)


def visible_prose(text: str) -> str:
    """Return reader-visible prose, excluding code and metadata."""
    text = re.sub(r"<!--(?:.*?-->|.*\Z)", "", text, flags=re.DOTALL)
    text = _strip_fenced_code(text)
    text = _strip_indented_code(text)
    text = _strip_inline_code(text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"!\[[^\]]*\]\[[^\]]*\]", "", text)
    text = re.sub(r"!\[[^\]]*\]", "", text)
    text = re.sub(r"^[ ]{0,3}\[[^\]\n]+\]:[^\n]*(?:\n|$)", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    collector = _VisibleHTMLCollector()
    collector.feed(text)
    collector.close()
    return "".join(collector.parts)


def validate_readme_contract(text: str) -> None:
    prose = visible_prose(text)
    for name in ("Apollo Dark", "Apollo Light"):
        if not re.search(rf"(?<![\w./-]){re.escape(name)}(?![\w./-])", prose):
            raise AssertionError(f"README contract missing visible name {name!r}")
    for label, marker in README_CONTRACT_MARKERS.items():
        if not re.search(rf"(?m)(?<!\S){re.escape(marker)}(?!\S)", text):
            raise AssertionError(f"README contract missing {label}")


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
    validate_readme_contract((ROOT / "README.md").read_text(encoding="utf-8"))
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
