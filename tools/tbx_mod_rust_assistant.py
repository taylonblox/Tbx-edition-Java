#!/usr/bin/env python3
"""TBX mod port assistant (safe Java JAR inspection + Rust adaptation workspace).

This is NOT a Java bytecode-to-Rust compiler. Java/Fabric/Forge mechanics
require manual porting to Horizon/Starling Rust hooks. Supported features:
- Inspect Fabric / Quilt / Forge manifests without running Java code.
- Catalog Java classes, mixins and resources; explain porting scope.
- Prepare an editable Rust crate skeleton and export assets/data as references.
- Refuse path traversal, symlinks, encrypted or oversized ZIP entries.
- No network calls, APK builds, Java execution, Cargo, or automatic installation.

Examples:
 python3 tools/tbx_mod_rust_assistant.py inspect mymod.jar --lang pt_br
 python3 tools/tbx_mod_rust_assistant.py prepare mymod.jar --output mymod_port --lang pt_br
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import tomllib
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

MAX_ARCHIVE = 220 * 1024 * 1024
MAX_ENTRIES = 12000
MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_RATIO = 500
MAX_PATH_CHARS = 240

@dataclass
class Scanned:
    path: Path
    entries: list[zipfile.ZipInfo]
    classes: list[str]
    resources: list[zipfile.ZipInfo]
    name: str
    mod_id: str
    version: str
    framework: str
    sha256: str

def valid_member(z: zipfile.ZipInfo) -> None:
    name = z.filename
    # The extraction tool must never trust an archive's provided path.
    p = PurePosixPath(name)
    if (not name or len(name) > MAX_PATH_CHARS or "\\" in name
            or name.startswith("/") or "\x00" in name
            or any(x in {"", ".", ".."} for x in name.rstrip("/").split("/"))
            or p.is_absolute() or z.flag_bits & 1):
        raise ValueError("Unsafe ZIP entry path or encryption")
    mode = (z.external_attr >> 16)
    if stat.S_ISLNK(mode):
        raise ValueError("Symlink entries are not allowed")
    if z.file_size > MAX_FILE:
        raise ValueError("A ZIP entry is larger than the safe per-file limit")
    if z.file_size and z.file_size / max(z.compress_size, 1) > MAX_RATIO:
        raise ValueError("Suspicious ZIP compression ratio")

def mod_metadata(archive: zipfile.ZipFile) -> tuple[str, str, str, str]:
    names = set(archive.namelist())
    for name, framework in [
        ("fabric.mod.json", "Fabric"),
        ("quilt.mod.json", "Quilt"),
    ]:
        if name not in names:
            continue
        j = json.loads(archive.read(name))
        if framework == "Quilt":
            mod = j.get("quilt_loader", {})
            return (str(mod.get("id", "unknown")),
                    str(mod.get("metadata", {}).get("name", mod.get("id", "Quilt mod"))),
                    str(mod.get("version", "unknown")), framework)
        return (str(j.get("id", "unknown")), str(j.get("name", j.get("id", "Fabric mod"))),
                str(j.get("version", "unknown")), framework)
    for path in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
        if path in names:
            content = tomllib.loads(archive.read(path).decode("utf-8"))
            entry = (content.get("mods") or [{}])[0]
            return (str(entry.get("modId", "unknown")), str(entry.get("displayName", "Forge mod")),
                    str(entry.get("version", "unknown")),
                    "NeoForge" if "neoforge" in path else "Forge")
    return ("unknown", "Unknown Java mod", "unknown", "Unknown")

def clean_id(text: str, fallback: str) -> str:
    ident = re.sub(r"[^a-z0-9_]", "_", text.strip().lower())
    ident = re.sub(r"_+", "_", ident).strip("_")
    if not ident or ident == "unknown":
        ident = re.sub(r"[^a-z0-9_]", "_", fallback.lower()).strip("_") or "imported_mod"
    return ident[:48]

def scan(path: Path) -> Scanned:
    path = path.resolve()
    if not path.is_file() or path.suffix.lower() not in {".jar", ".zip"}:
        raise ValueError("Select a valid .jar or .zip file")
    if path.stat().st_size > MAX_ARCHIVE:
        raise ValueError("Archive too large")
    with zipfile.ZipFile(path) as zf:
        entries = zf.infolist()
        if len(entries) > MAX_ENTRIES:
            raise ValueError("Too many archive entries")
        size_sum = 0
        seen = set()
        for entry in entries:
            valid_member(entry)
            if entry.filename in seen:
                raise ValueError("Duplicate ZIP paths are not allowed")
            seen.add(entry.filename)
            size_sum += entry.file_size
            if size_sum > MAX_TOTAL:
                raise ValueError("Archive uncompressed size exceeds limit")
        raw_id, raw_name, version, framework = mod_metadata(zf)
        classes = sorted(e.filename for e in entries if e.filename.endswith(".class"))
        resources = [e for e in entries if not e.is_dir() and
                     (e.filename.startswith("assets/") or e.filename.startswith("data/"))]
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return Scanned(path, entries, classes, resources, str(raw_name)[:120],
                   clean_id(raw_id, path.stem), str(version)[:80], framework, h.hexdigest())

def report(mod: Scanned, pt: bool) -> dict:
    methods = bool(mod.classes)
    return {
        "format": "tbx-rust-port-analysis-v1",
        "source_filename": mod.path.name,
        "source_sha256": mod.sha256,
        "mod_id": mod.mod_id,
        "mod_name": mod.name,
        "version": mod.version,
        "loader": mod.framework,
        "java_class_count": len(mod.classes),
        "resource_file_count": len(mod.resources),
        "java_class_examples": mod.classes[:20],
        "needs_manual_rust_port": methods,
        "playable": False,
        "compiled": False,
        "notes": (
            [
                "Este relatório NÃO converte código Java em Rust.",
                "As classes .class, mixins, APIs Fabric/Forge e lógica do mod precisam ser reimplementados.",
                "Somente os recursos das pastas assets/ e data/ são separados para análise.",
                "O projeto Rust gerado é um esqueleto de desenvolvimento, não um .hnmod funcional.",
                "Revise as licenças antes de redistribuir recursos de outros criadores.",
            ] if pt else [
                "This report does NOT convert Java bytecode to Rust.",
                "Java classes, mixins, Fabric/Forge APIs, and game logic require manual reimplementation.",
                "Only assets/ and data/ files are extracted for inspection.",
                "The Rust crate is a development skeleton, not a working .hnmod.",
                "Check third-party asset licenses before redistribution.",
            ]
        ),
    }

def prepare(mod: Scanned, output: Path, pt: bool) -> None:
    output = output.resolve()
    if output.exists():
        raise ValueError("Output path already exists; choose a new empty folder")
    # Never write on top of an existing project or input archive.
    if output == mod.path or mod.path in output.parents:
        raise ValueError("Invalid destination")
    output.mkdir(parents=True)
    (output / "src").mkdir()
    (output / "resources").mkdir()
    with zipfile.ZipFile(mod.path) as zf:
        for item in mod.resources:
            dst = output / "resources" / item.filename
            # Path validation already rejected traversal and backslashes.
            dst.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(item) as src, dst.open("wb") as target:
                remaining = item.file_size
                while remaining:
                    chunk = src.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError(f"Unexpected EOF in {item.filename}")
                    target.write(chunk)
                    remaining -= len(chunk)
    ident = clean_id("tbx_port_" + mod.mod_id, "tbx_port")
    (output / "Cargo.toml").write_text(
        f'[package]\nname = "{ident}"\nversion = "0.1.0"\nedition = "2021"\n'
        '\n[lib]\ncrate-type = ["rlib"]\n\n[dependencies]\n',
        encoding="utf-8")
    (output / "src/lib.rs").write_text(
        '//! TBX migration scaffold. NOT connected to the game.\n'
        '//! Port behavior to the supported Horizon native hooks deliberately.\n'
        '//! Do not claim support merely because this skeleton compiles.\n'
        f'pub const ORIGINAL_MOD_ID: &str = "{mod.mod_id}";\n'
        f'pub const ORIGINAL_JAVA_CLASS_COUNT: usize = {len(mod.classes)};\n'
        '\n// TODO: examine mappings, mod behavior, and supported native hook APIs.\n'
        '// TODO: write focused tests and a Horizon mixin manifest when ported.\n',
        encoding="utf-8")
    (output / "analysis.json").write_text(
        json.dumps(report(mod, pt), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    howto = (
        "# Adaptação de mod Java para TBX (em desenvolvimento)\n\n"
        "1. Veja analysis.json. Nenhuma classe Java foi convertida automaticamente.\n"
        "2. Confira a pasta resources e as licenças antes de usar os recursos.\n"
        "3. Reimplemente os comportamentos usando os hooks Rust do Horizon.\n"
        "4. Crie um pacote .hnmod real somente depois de implementar e testar.\n"
        "5. No Starling, Compilar funciona para um .hnmod compatível, não para .jar.\n"
        "\n**Este projeto não é jogável. Nenhum APK foi gerado.**\n"
        if pt else
        "# Java mod to TBX port (work in progress)\n\n"
        "1. Read analysis.json. No Java classes were converted automatically.\n"
        "2. Check resources and license rights before reuse.\n"
        "3. Reimplement behaviors through Horizon's supported Rust hooks.\n"
        "4. Create a .hnmod only once behavior is implemented and tested.\n"
        "5. Starling's Compile button is for compatible .hnmod, not .jar.\n"
        "\n**This project is not playable. No APK was built.**\n"
    )
    (output / "PORTING.md").write_text(howto, encoding="utf-8")

def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="command", required=True)
    for name in ("inspect", "prepare"):
        p = sub.add_parser(name)
        p.add_argument("mod", type=Path)
        p.add_argument("--lang", default="pt_br", choices=["pt_br", "en_us"])
        if name == "prepare":
            p.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    try:
        mod = scan(args.mod)
        if args.command == "prepare":
            prepare(mod, args.output, args.lang == "pt_br")
            print(("Pasta de análise criada: " if args.lang == "pt_br" else "Port workspace: ") + str(args.output))
        print(json.dumps(report(mod, args.lang == "pt_br"), indent=2, ensure_ascii=False))
    except (ValueError, OSError, zipfile.BadZipFile, UnicodeError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        print(("Erro ao analisar o mod: " if args.lang == "pt_br" else "Mod analysis error: ") + str(exc), file=sys.stderr)
        raise SystemExit(2)

if __name__ == "__main__":
    main()
