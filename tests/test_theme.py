from __future__ import annotations

import importlib.util
import pathlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate = load_module("rmux_generate", ROOT / "scripts" / "generate.py")
check = load_module("rmux_check", ROOT / "scripts" / "check.py")


class ApolloRmuxThemeTests(unittest.TestCase):
    def test_artifact_is_deterministic_and_theme_only(self) -> None:
        self.assertEqual(
            (ROOT / "apollo-rmux.conf").read_text(encoding="utf-8"),
            generate.render(generate.load_palette()),
        )
        check.validate_theme_only()

    @unittest.skipUnless(check.compatible_binary(), "neither rmux nor tmux is installed")
    def test_isolated_rmux_compatible_server_applies_apollo_options(self) -> None:
        binary = check.compatible_binary()
        assert binary
        check.validate_isolated_server(binary)


if __name__ == "__main__":
    unittest.main()
