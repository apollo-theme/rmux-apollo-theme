# Apollo for RMUX

A standalone RMUX theme, separate from the tmux package as requested. `apollo-rmux.conf` contains only RMUX/tmux-compatible color options; it does not copy status content, key bindings, prefixes, commands, or unrelated RMUX configuration.

Repository: https://github.com/apollo-theme/rmux-apollo-theme

## Install

Clone without modifying your RMUX configuration:

```sh
git clone https://github.com/apollo-theme/rmux-apollo-theme "$HOME/.config/rmux-apollo-theme"
```

## Activate

Apply it to the running RMUX daemon:

```sh
rmux source-file "$HOME/.config/rmux-apollo-theme/apollo-rmux.conf"
```

For future daemons, manually add this line to your RMUX configuration:

```tmux
source-file ~/.config/rmux-apollo-theme/apollo-rmux.conf
```

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
