#!/usr/bin/env python3
"""TBX installer compatibility preflight (metadata only, no Java execution).

The existing Starling in-game catalog resolves and installs supported native
dependencies. This tool explains a manually imported Java .jar and lists
its declared dependencies before any port-to-Rust attempt. It does NOT
install .jar mods or pretend they are Rust/native Minecraft mods.
"""
import argparse
import json
import zipfile
from pathlib import Path
from tbx_mod_rust_assistant import scan

def required(jar: Path) -> list[dict[str, str]]:
    result = []
    with zipfile.ZipFile(jar) as z:
        names = set(z.namelist())
        if "fabric.mod.json" in names:
            j = json.loads(z.read("fabric.mod.json"))
            for mod, version in (j.get("depends") or {}).items():
                result.append({"mod": str(mod), "version": str(version), "loader": "Fabric"})
        if "quilt.mod.json" in names:
            j = json.loads(z.read("quilt.mod.json"))
            deps = j.get("quilt_loader", {}).get("depends", [])
            for dep in deps:
                if not isinstance(dep, dict): continue
                ident = dep.get("id")
                if ident is not None:
                    result.append({"mod": str(ident), "version": str(dep.get("versions", "*")),
                                   "loader": "Quilt"})
        for p in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
            if p not in names: continue
            import tomllib
            j = tomllib.loads(z.read(p).decode("utf-8"))
            for group in (j.get("dependencies") or {}).values():
                for dep in group if isinstance(group, list) else [group]:
                    if isinstance(dep, dict) and dep.get("mandatory", dep.get("type") == "required"):
                        result.append({"mod": str(dep.get("modId", "")),
                                       "version": str(dep.get("versionRange", "*")),
                                       "loader": "NeoForge" if "neoforge" in p else "Forge"})
    # Limit untrusted metadata from filling Android memory.
    return sorted(result[:256], key=lambda x: (x["mod"], x["version"]))

def preflight(jar: Path, pt: bool = True):
    mod = scan(jar)
    deps = required(mod.path)
    return {
        "source_file": mod.path.name,
        "loader": mod.framework,
        "java_classes": len(mod.classes),
        "declared_dependencies": deps,
        "automatically_compatible_with_tbx": False,
        "native_starling_compile_supported": False,
        "manual_rust_port_required": bool(mod.classes),
        "message": (
            "Arquivo Java .jar: nao sera instalado nem executado como mod nativo. "
            "As dependencias sao apenas informativas; adaptar para Rust exige reimplementar codigo."
            if pt else
            "Java .jar cannot be installed or run as a native mod. Dependencies are for "
            "inspection only; a Rust port requires manual reimplementation."
        )
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("jar", type=Path)
    p.add_argument("--lang", choices=["pt_br","en_us"], default="pt_br")
    a = p.parse_args()
    print(json.dumps(preflight(a.jar,a.lang=="pt_br"),indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
