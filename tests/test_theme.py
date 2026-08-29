from __future__ import annotations

import hashlib
import importlib.util
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
    def test_both_variants_are_deterministic_and_theme_only(self) -> None:
        self.assertEqual(
            hashlib.sha256((ROOT / "palette" / "apollo-light.json").read_bytes()).hexdigest(),
            "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        )
        expected = generate.render_outputs()
        self.assertEqual(set(expected), {ROOT / "apollo-rmux.conf", ROOT / "apollo-rmux-light.conf"})
        for path, text in expected.items():
            self.assertEqual(path.read_text(encoding="utf-8"), text)
            check.validate_theme_only(path)

    @unittest.skipUnless(check.compatible_binary(), "neither rmux nor tmux is installed")
    def test_isolated_rmux_compatible_server_applies_both_variants(self) -> None:
        binary = check.compatible_binary()
        assert binary
        for variant in ("dark", "light"):
            with self.subTest(variant=variant):
                check.validate_isolated_server(binary, variant)


if __name__ == "__main__":
    unittest.main()
