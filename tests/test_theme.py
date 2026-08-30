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

    def test_readme_contract_requires_visible_names_and_exact_usage_markers(self) -> None:
        hidden = """<!-- Apollo Dark --><img alt="Apollo Light">
<span hidden>Apollo Dark</span>
<span aria-hidden="true">Apollo Light</span>
`Apollo Dark` `Apollo Light.conf`
```text
Apollo Dark
Apollo Light
```
    Apollo Dark
	Apollo Light
[Apollo Dark]: https://example.invalid/dark
[Apollo Light]: https://example.invalid/light
"""
        self.assertNotIn("Apollo Dark", check.visible_prose(hidden))
        self.assertNotIn("Apollo Light", check.visible_prose(hidden))
        unclosed_comment = check.visible_prose(
            "Visible before comment.<!-- Apollo Dark\nApollo Light"
        )
        self.assertIn("Visible before comment.", unclosed_comment)
        self.assertNotIn("Apollo Dark", unclosed_comment)
        self.assertNotIn("Apollo Light", unclosed_comment)
        hidden_html = """Visible start.
<span aria-hidden=true>Apollo Dark</span>
<span aria-hidden='true'>Apollo Light</span>
<span aria-hidden="true">Apollo Dark</span>
<span hidden><strong>Apollo Light</strong><span aria-hidden=false>Apollo Dark</span></span>
<code>Apollo Light</code><script>Apollo Dark</script><style>Apollo Light</style>
<template>Apollo Dark</template><img alt="Apollo Light">
<div hidden>Apollo Dark
Visible end.
"""
        hidden_prose = check.visible_prose(hidden_html)
        self.assertNotIn("Apollo Dark", hidden_prose)
        self.assertNotIn("Apollo Light", hidden_prose)
        self.assertIn("Visible start.", hidden_prose)
        self.assertNotIn("Visible end.", hidden_prose)
        styled_hidden = check.visible_prose("""Visible style start.
<pre>Apollo Dark</pre>
<div style=" DISPLAY : NoNe !IMPORTANT "><span aria-hidden=false>Apollo Dark</span></div>
<div style=' visibility : HIDDEN !important '><strong>Apollo Light</strong></div>
<span style=display:none>Apollo Light</span>
Visible style end.
""")
        self.assertNotIn("Apollo Dark", styled_hidden)
        self.assertNotIn("Apollo Light", styled_hidden)
        self.assertIn("Visible style start.", styled_hidden)
        self.assertIn("Visible style end.", styled_hidden)
        malformed = check.visible_prose(
            "Visible before.<span hidden>Apollo Dark</div>Apollo Light</span>Visible after."
        )
        self.assertNotIn("Apollo Dark", malformed)
        self.assertNotIn("Apollo Light", malformed)
        self.assertIn("Visible before.", malformed)
        self.assertIn("Visible after.", malformed)
        visible_html = """<span aria-hidden=false>Apollo Dark</span>
<span aria-hidden='false'>Apollo Light</span>
<span aria-hidden="false">Apollo Dark and Apollo Light</span>
<span style="display: block; visibility: visible">Apollo Dark and Apollo Light</span>"""
        visible_html_prose = check.visible_prose(visible_html)
        self.assertIn("Apollo Dark", visible_html_prose)
        self.assertIn("Apollo Light", visible_html_prose)
        fenced_code_cases = (
            "Visible before.\n   ```python\nApollo Dark\n   ````   \nVisible after.\n",
            "Visible before.\n  ~~~\nApollo Light\n  ~~~~\t \nVisible after.\n",
        )
        for source in fenced_code_cases:
            with self.subTest(fenced_code=source):
                prose = check.visible_prose(source)
                self.assertNotIn("Apollo Dark", prose)
                self.assertNotIn("Apollo Light", prose)
                self.assertIn("Visible before.", prose)
                self.assertIn("Visible after.", prose)
        for unmatched_fence in (
            "Visible before.\n```text\nApollo Dark\n~~~   \nVisible after.\n",
            "Visible before.\n```text\nApollo Dark\n``   \nVisible after.\n",
            "Visible before.\n~~~\nApollo Light\n",
        ):
            with self.subTest(unmatched_fence=unmatched_fence):
                self.assertEqual(check.visible_prose(unmatched_fence), unmatched_fence)
        blockquoted_fence = (
            "> Ordinary blockquote prose.\n"
            ">   ```text\n> Apollo Dark\n> Apollo Light\n>   ````   \n"
            "> Ordinary trailing blockquote prose.\nVisible trailing text.\n"
        )
        blockquoted_fence_prose = check.visible_prose(blockquoted_fence)
        self.assertNotIn("Apollo Dark", blockquoted_fence_prose)
        self.assertNotIn("Apollo Light", blockquoted_fence_prose)
        self.assertIn("Ordinary blockquote prose.", blockquoted_fence_prose)
        self.assertIn("Ordinary trailing blockquote prose.", blockquoted_fence_prose)
        self.assertIn("Visible trailing text.", blockquoted_fence_prose)
        list_fence_cases = (
            (
                "Apollo Dark",
                "- Visible unordered list prose before.\n"
                "- ~~~text\n  Apollo Dark\n  ~~~~   \n"
                "- Visible unordered list prose after.\nVisible trailing text.\n",
            ),
            (
                "Apollo Light",
                "1. Visible ordered list prose before.\n"
                "2. ```text\n   Apollo Light\n   ````\t \n"
                "3. Visible ordered list prose after.\nVisible trailing text.\n",
            ),
        )
        for name, source in list_fence_cases:
            with self.subTest(list_fence=name):
                prose = check.visible_prose(source)
                self.assertNotIn(name, prose)
                self.assertIn("list prose before.", prose)
                self.assertIn("list prose after.", prose)
                self.assertIn("Visible trailing text.", prose)
        list_indented = (
            "- Visible unordered list prose before.\n"
            "-     Apollo Dark\n"
            "- Visible unordered list prose after.\n"
            "1. Visible ordered list prose before.\n"
            "2.     Apollo Light\n"
            "3. Visible ordered list prose after.\n"
            "Visible trailing text.\n"
        )
        list_indented_prose = check.visible_prose(list_indented)
        self.assertNotIn("Apollo Dark", list_indented_prose)
        self.assertNotIn("Apollo Light", list_indented_prose)
        self.assertIn("unordered list prose before.", list_indented_prose)
        self.assertIn("unordered list prose after.", list_indented_prose)
        self.assertIn("ordered list prose before.", list_indented_prose)
        self.assertIn("ordered list prose after.", list_indented_prose)
        self.assertIn("Visible trailing text.", list_indented_prose)
        mixed_indented = (
            "Visible mixed prose before.\n"
            " \tApollo Dark\n"
            "   \tApollo Light\n"
            "Visible mixed prose after.\n"
            "- Visible mixed list prose before.\n"
            "-  \tApollo Dark\n"
            "1.    \tApollo Light\n"
            "- Visible mixed list prose after.\n"
            "Visible mixed trailing text.\n"
        )
        mixed_indented_prose = check.visible_prose(mixed_indented)
        self.assertNotIn("Apollo Dark", mixed_indented_prose)
        self.assertNotIn("Apollo Light", mixed_indented_prose)
        self.assertIn("Visible mixed prose before.", mixed_indented_prose)
        self.assertIn("Visible mixed prose after.", mixed_indented_prose)
        self.assertIn("Visible mixed list prose before.", mixed_indented_prose)
        self.assertIn("Visible mixed list prose after.", mixed_indented_prose)
        self.assertIn("Visible mixed trailing text.", mixed_indented_prose)
        blockquoted_indented = (
            "> Ordinary blockquote prose.\n"
            ">     Apollo Dark\n> \tApollo Light\n"
            "> Ordinary trailing blockquote prose.\nVisible trailing text.\n"
        )
        blockquoted_indented_prose = check.visible_prose(blockquoted_indented)
        self.assertNotIn("Apollo Dark", blockquoted_indented_prose)
        self.assertNotIn("Apollo Light", blockquoted_indented_prose)
        self.assertIn("Ordinary blockquote prose.", blockquoted_indented_prose)
        self.assertIn("Ordinary trailing blockquote prose.", blockquoted_indented_prose)
        self.assertIn("Visible trailing text.", blockquoted_indented_prose)
        self.assertEqual(
            check.visible_prose("```Apollo Dark``` visible after."),
            " visible after.",
        )
        escaped_backticks = r"Visible before \`Apollo Dark\` and \`Apollo Light\` visible after."
        self.assertEqual(check.visible_prose(escaped_backticks), escaped_backticks)
        inline_code_cases = (
            ("Apollo Dark", "Visible before ``Apollo Dark`` visible after."),
            ("Apollo Light", "Visible before ```Apollo Light``` visible after."),
            ("Apollo Dark", "Visible before `` Apollo Dark `` visible after."),
            ("Apollo Light", "Visible before ```  Apollo Light  ``` visible after."),
            ("Apollo Dark", "Visible before ```` Apollo Dark ```` visible after."),
        )
        for name, source in inline_code_cases:
            with self.subTest(inline_code=source):
                prose = check.visible_prose(source)
                self.assertNotIn(name, prose)
                self.assertIn("Visible before ", prose)
                self.assertIn(" visible after.", prose)
        self.assertEqual(
            check.visible_prose("Visible before `` `` visible after."),
            "Visible before  visible after.",
        )
        multiline_inline = check.visible_prose(
            "Visible before ``Apollo Dark\nApollo Light`` visible after."
        )
        self.assertNotIn("Apollo Dark", multiline_inline)
        self.assertNotIn("Apollo Light", multiline_inline)
        self.assertIn("Visible before ", multiline_inline)
        self.assertIn(" visible after.", multiline_inline)
        for unmatched in (
            "Visible before ```` visible after.",
            "Visible before ``Apollo Dark visible after.",
            "Visible before ``Apollo Dark``` visible after.",
            "Visible before ``Apollo Dark\nApollo Light``` visible after.",
        ):
            with self.subTest(unmatched=unmatched):
                self.assertEqual(check.visible_prose(unmatched), unmatched)
        self.assertIn(
            "Apollo Dark and Apollo Light",
            check.visible_prose("[Apollo Dark](dark) and [Apollo Light](light)"),
        )
        image_markdown = """![Apollo Dark](dark.png)
![Apollo Light][light-image]
![Apollo Dark][]
![Apollo Light]
[Apollo Dark]: dark.png
[Apollo Light]: light.png
[light-image]: light.png
"""
        image_prose = check.visible_prose(image_markdown)
        self.assertNotIn("Apollo Dark", image_prose)
        self.assertNotIn("Apollo Light", image_prose)
        link_markdown = """[Apollo Dark](dark)
[Apollo Light][light-link]
[Apollo Dark][]
[Apollo Light]
[Apollo Dark]: dark
[Apollo Light]: light
[light-link]: light
"""
        link_prose = check.visible_prose(link_markdown)
        self.assertIn("Apollo Dark", link_prose)
        self.assertIn("Apollo Light", link_prose)
        filename_cases = {
            "Apollo Dark": "Apollo Dark.conf\nApollo Light is visible.\n",
            "Apollo Light": "Apollo Dark is visible.\nApollo Light.conf\n",
        }
        for name, filename_only in filename_cases.items():
            with self.subTest(filename=name):
                with self.assertRaises(AssertionError) as caught:
                    check.validate_readme_contract(filename_only)
                self.assertEqual(str(caught.exception), f"README contract missing visible name {name!r}")

        markers = {
            "dark source command": 'rmux source-file "$HOME/.config/rmux-apollo-theme/apollo-rmux.conf"',
            "light source command": 'rmux source-file "$HOME/.config/rmux-apollo-theme/apollo-rmux-light.conf"',
            "dark status output": "bg=#141617,fg=#cfbc97",
            "light status output": "bg=#f9f5d7,fg=#3c3836",
        }
        fixture = (
            "[Apollo Dark](dark) and [Apollo Light](light) remain compatible.\n"
            "```sh\n" + "\n".join(markers.values()) + "\n```\n"
        )
        check.validate_readme_contract(fixture)
        mutations = {
            "visible name 'Apollo Dark'": fixture.replace("[Apollo Dark]", "[Dark]"),
            "visible name 'Apollo Light'": fixture.replace("[Apollo Light]", "[Light]"),
            **{label: fixture.replace(marker, "") for label, marker in markers.items()},
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label):
                with self.assertRaises(AssertionError) as caught:
                    check.validate_readme_contract(mutated)
                self.assertEqual(str(caught.exception), f"README contract missing {label}")
        for label, marker in markers.items():
            for affix, mutated in (
                ("prefix", fixture.replace(marker, f"x{marker}", 1)),
                ("suffix", fixture.replace(marker, f"{marker}x", 1)),
            ):
                with self.subTest(label=label, affix=affix):
                    with self.assertRaises(AssertionError) as caught:
                        check.validate_readme_contract(mutated)
                    self.assertEqual(str(caught.exception), f"README contract missing {label}")

        check.validate_readme_contract((ROOT / "README.md").read_text(encoding="utf-8"))

    @unittest.skipUnless(check.compatible_binary(), "neither rmux nor tmux is installed")
    def test_isolated_rmux_compatible_server_applies_both_variants(self) -> None:
        binary = check.compatible_binary()
        assert binary
        for variant in ("dark", "light"):
            with self.subTest(variant=variant):
                check.validate_isolated_server(binary, variant)


if __name__ == "__main__":
    unittest.main()
