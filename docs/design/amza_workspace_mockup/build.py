#!/usr/bin/env python3
"""Rebuild amza_workspace_mockup.html from template.html + data.json.

Run from anywhere:  python docs/design/amza_workspace_mockup/build.py
"""
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent.parent
LOGO_PATH = REPO_ROOT / "amza-logo.png"
FONT_PATH = ROOT / "manrope.woff2"
OUTPUT_PATH = ROOT / "amza_workspace_mockup.html"


def build() -> None:
    template = (ROOT / "template.html").read_text()
    logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    font_b64 = base64.b64encode(FONT_PATH.read_bytes()).decode()
    data_json = (ROOT / "data.json").read_text().strip()

    output = (
        template.replace("__LOGO_B64__", logo_b64)
        .replace("__FONT_B64__", font_b64)
        .replace("__DATA_JSON__", data_json)
    )
    OUTPUT_PATH.write_text(output)
    print(f"Built {OUTPUT_PATH} ({len(output)} bytes)")


if __name__ == "__main__":
    build()
