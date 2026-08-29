<h1 align="center">RMUX Apollo Theme</h1>

<p align="center">A standalone, theme-only RMUX configuration built with the canonical Apollo palette.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-rmux"><img alt="Preview" src="https://img.shields.io/badge/Preview-Website-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/rmux-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/rmux-apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/rmux-apollo-theme/releases/latest"><img alt="Latest Release" src="https://img.shields.io/github/v/release/apollo-theme/rmux-apollo-theme?sort=semver&amp;style=flat-square&amp;label=Release&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-b8bb26?style=flat-square&amp;labelColor=141617"></a>
  <a href="apollo-rmux.conf"><img alt="Target RMUX" src="https://img.shields.io/badge/Target-RMUX-83a598?style=flat-square&amp;labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical palette" src="https://img.shields.io/badge/palette-canonical-fabd2f?style=flat-square&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-rmux"><img alt="RMUX Apollo Dark simulated preview" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/rmux.svg" width="900"></a>
  <a href="https://apollo-theme.github.io/#app-rmux-light"><img alt="RMUX Apollo Light simulated preview" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/rmux-light.svg" width="900"></a>
</p>

<p align="center"><em>Simulated preview — terminal fonts and rendering can change the final appearance.</em></p>

## About

This standalone RMUX repository remains separate from the tmux package. `apollo-rmux.conf` (Dark) and `apollo-rmux-light.conf` (Light) contain only RMUX/tmux-compatible color options; neither copies status content, key bindings, prefixes, commands, hooks, or unrelated RMUX configuration. Source exactly one variant at a time.

Repository: <https://github.com/apollo-theme/rmux-apollo-theme>

## Install

Clone without modifying your RMUX configuration:

```sh
git clone https://github.com/apollo-theme/rmux-apollo-theme "$HOME/.config/rmux-apollo-theme"
```

## Activate

Apply exactly one variant to the running RMUX daemon:

```sh
# Dark (default)
rmux source-file "$HOME/.config/rmux-apollo-theme/apollo-rmux.conf"

# Light
rmux source-file "$HOME/.config/rmux-apollo-theme/apollo-rmux-light.conf"
```

For future daemons, manually add one corresponding `source-file` line to your RMUX configuration. Do not source both variants; the last one would replace the same theme options. RMUX controls its status, pane-border, message, and mode chrome but cannot change the terminal canvas behind pane content, so pair Apollo Light with a light terminal profile.

No installer edits `rmux.conf`.

## Uninstall

Remove the `source-file` line, then remove the clone:

```sh
rm -rf "$HOME/.config/rmux-apollo-theme"
```

A running daemon keeps its current option values; reload your normal theme/configuration or restart RMUX when safe.

## Visual check

Attach to RMUX. The status canvas should be near-black with warm text, the active window blue, active pane borders and messages gold, and alerts red. Confirm the base status values with:

```sh
rmux show-options -gv status-style
# bg=#141617,fg=#cfbc97
```

## Development

The checker prefers installed `rmux` and otherwise validates the source in an isolated compatible tmux server.

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```
