# RMUX Apollo theme development

- `palette/apollo.json` is the exact canonical snapshot. Update the pinned SHA-256 in `scripts/generate.py` only when deliberately refreshing it.
- Edit `scripts/generate.py`, not generated `apollo-rmux.conf`.
- Keep RMUX separate and theme-only: no unrelated rmux.conf content, keys, prefix, status content, commands, or hooks.
- Generate: `python3 scripts/generate.py`
- Check with isolated RMUX (or compatible tmux fallback): `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloRmuxThemeTests.test_isolated_rmux_compatible_server_applies_apollo_options`
