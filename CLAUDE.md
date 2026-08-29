# RMUX Apollo theme development

- `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots. Update pinned SHA-256 values only when deliberately refreshing them.
- Edit `scripts/generate.py`, not generated `apollo-rmux.conf` or `apollo-rmux-light.conf`.
- Keep both RMUX variants separate and theme-only: no unrelated rmux.conf content, keys, prefix, status content, commands, or hooks. Users source exactly one variant.
- Generate: `python3 scripts/generate.py`
- Check with isolated RMUX (or compatible tmux fallback): `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloRmuxThemeTests.test_isolated_rmux_compatible_server_applies_apollo_options`
