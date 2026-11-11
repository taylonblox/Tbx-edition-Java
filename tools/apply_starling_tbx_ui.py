#!/usr/bin/env python3
"""Apply TBX blue UI and remove the extra HUD settings gear on Starling source.

Upstream reference: starling-client/starling, tag v0.8.0
Pinned commit: ac874422ed8f892505ff73d67ae486ecfee7a516

Run from any machine with Python 3:
  python3 apply_starling_tbx_ui.py /path/to/starling --check
  python3 apply_starling_tbx_ui.py /path/to/starling

This script ONLY changes Rust source. It NEVER builds, signs, or exports an APK.
The original TBX Edition V1.0.4 code and Android signing identity are not
reconstructed by this patch. The Starling port remains a separate experiment.

Changes are staged in memory; if any expected upstream anchor has moved,
the script stops BEFORE modifying files instead of silently making a partial
or unsafe migration. Rerunning is safe when the files are already patched.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def swap(text: str, before: str, after: str, label: str) -> str:
    """Require one exact original anchor (or an already-applied patch)."""
    count = text.count(before)
    if count == 1:
        return text.replace(before, after, 1)
    if count == 0 and after in text:
        return text
    raise ValueError(f"{label}: unexpected upstream changes (matches={count})")


def field(text: str, block_name: str, field_name: str, old: str, new: str) -> str:
    """Change a single color token in one named Rust const block."""
    marker = "pub const " + block_name + ":"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"missing {block_name}")
    end = text.find("\n};", start)
    if end < 0:
        raise ValueError(f"unterminated {block_name}")
    chunk = text[start:end]
    chunk = swap(chunk, f"    {field_name}: {old},",
                 f"    {field_name}: {new},", f"{block_name}.{field_name}")
    return text[:start] + chunk + text[end:]


def controls(text: str) -> str:
    return swap(
        text,
        "    pub fn visible(&self, c: Control) -> bool {\n"
        "        if c == Control::Shield && !self.shield_available && self.editor.is_none() {",
        "    pub fn visible(&self, c: Control) -> bool {\n"
        "        // TBX: hide the extra in-game settings gear everywhere, including\n"
        "        // custom touch layouts. This also removes its hitbox. The regular\n"
        "        // pause/options screens and control editor remain accessible.\n"
        "        if c == Control::Settings {\n"
        "            return false;\n"
        "        }\n"
        "        if c == Control::Shield && !self.shield_available && self.editor.is_none() {",
        "android_controls::visible",
    )


def palette(text: str) -> str:
    changes = {
        "LIGHT": [("accent", "0x5b3fd6", "0x155bd4")],
        "DARK": [("accent", "0x9a86ff", "0x60a5fa")],
        "BLOCKS_DARK": [
            ("accent", "0x9a86ff", "0x60a5fa"),
            ("face", "0x5b3fd6", "0x1d4ed8"),
            ("face_bevel", "0x8a74ff", "0x3b82f6"),
            ("face_lip", "0x3a2694", "0x1e3a8a"),
        ],
        "BLOCKS_LIGHT": [
            ("accent", "0x5333c9", "0x1e40af"),
            ("face", "0x5b3fd6", "0x1d4ed8"),
            ("face_bevel", "0x8069ef", "0x60a5fa"),
            ("face_lip", "0x3a2694", "0x1e3a8a"),
        ],
    }
    for block, entries in changes.items():
        for name, old, new in entries:
            text = field(text, block, name, old, new)
    return text


def glass(text: str) -> str:
    return swap(text, "pub const ACCENT: u32 = 0x6b4bff;",
                "pub const ACCENT: u32 = 0x2563eb;", "glass accent")


def night(text: str) -> str:
    for block, changes in {
        "NIGHT": [
            ("accent", "0x7656fa", "0x2563eb"),
            ("accent_hi", "0xa08cff", "0x93c5fd"),
        ],
        "DAWN": [
            ("accent", "0x5b3fd6", "0x1d4ed8"),
            ("accent_hi", "0x5333c9", "0x1e40af"),
        ],
    }.items():
        for name, old, new in changes:
            text = field(text, block, name, old, new)
    return text


def android_theme(text: str) -> str:
    replacements = [
        (
            "pub enum ThemePreset {\n    #[default]\n    ObsidianViolet,",
            "pub enum ThemePreset {\n    #[default]\n    TbxBlue,\n    ObsidianViolet,",
            "preset enum",
        ),
        (
            "pub const ALL: [Self; 8] = [\n        Self::ObsidianViolet,",
            "pub const ALL: [Self; 9] = [\n        Self::TbxBlue,\n        Self::ObsidianViolet,",
            "preset list",
        ),
        (
            'match self {\n            Self::ObsidianViolet => "Obsidian Violet",',
            'match self {\n            Self::TbxBlue => "TBX Blue",\n'
            '            Self::ObsidianViolet => "Obsidian Violet",',
            "preset label",
        ),
        (
            'match self {\n            Self::ObsidianViolet => "Signature Horizon dark violet",',
            'match self {\n            Self::TbxBlue => "TBX dark with bright blue buttons",\n'
            '            Self::ObsidianViolet => "Signature Horizon dark violet",',
            "preset subtitle",
        ),
        (
            "match self {\n            Self::ObsidianViolet | Self::Custom => (",
            "match self {\n"
            "            Self::TbxBlue => (\n"
            "                0x0B1426, 0x132642, 0x2477FF, 0x0E1C38, 0x16315A, 0x091324, false,\n"
            "            ),\n"
            "            Self::ObsidianViolet | Self::Custom => (",
            "preset RGB",
        ),
        (
            "preset: ThemePreset::ObsidianViolet,",
            "preset: ThemePreset::TbxBlue,",
            "default TBX theme",
        ),
        (
            'custom_accent_hex: "#9A7BFF".into(),',
            'custom_accent_hex: "#2477FF".into(),',
            "default accent",
        ),
        (
            '(0x9A7BFF, "#9A7BFF", "Violet"),',
            '(0x2477FF, "#2477FF", "TBX Blue"),',
            "accent swatch",
        ),
    ]
    for old, new, label in replacements:
        text = swap(text, old, new, label)
    return text


def android_control_ui(text: str) -> str:
    return swap(text, '(0xFF9A7BFF, "Violet"),',
                '(0xFF2477FF, "TBX Blue"),',
                "touch editor color swatch")


TRANSFORMS = {
    "crates/horizon-client-render/src/android_controls.rs": controls,
    "crates/horizon-theme/src/lib.rs": palette,
    "crates/horizon-theme/src/glass.rs": glass,
    "crates/horizon-theme/src/night.rs": night,
    "crates/horizon-client/src/android_control_theme.rs": android_theme,
    "crates/horizon-client/src/android_control_ui.rs": android_control_ui,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("starling_source", type=Path)
    parser.add_argument("--check", action="store_true",
                        help="Audit anchors and intended changes without writing anything")
    args = parser.parse_args()
    root = args.starling_source.resolve()
    if not (root / "Cargo.toml").is_file():
        parser.error("expected a Starling/Horizon source checkout with Cargo.toml")

    # Atomic preflight: all 6 files must be readable and transform successfully
    # before changing even one file.
    files = {}
    changed = []
    for relative, transform in TRANSFORMS.items():
        path = root / relative
        original = path.read_text(encoding="utf-8")
        updated = transform(original)
        files[path] = updated
        if updated != original:
            changed.append(relative)

    if args.check:
        print("PASS: all 6 source targets are compatible with the TBX overlay.")
        print("Would update:", ", ".join(changed) or "nothing (already applied)")
        return

    for path, content in files.items():
        if str(path.relative_to(root)) in changed:
            path.write_text(content, encoding="utf-8")
    print("TBX Starling UI overlay applied to", len(changed), "source files.")
    print("Extra settings HUD gear: hidden; blue accents: ready.")
    print("NO APK was built. Source compilation and integration tests are still required.")


if __name__ == "__main__":
    main()
