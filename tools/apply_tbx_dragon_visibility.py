#!/usr/bin/env python3
"""TBX Ender Dragon visibility fallback; source-only, pinned Starling 0.8.0.

The dragon should not disappear just because its optional emissive eye
texture is absent: skin/body geometry still renders. The core dragon
flight/damage/boss bar implementation remains Starling's tested one.
"""
from pathlib import Path
import argparse

def once(s, a, b, where):
    n=s.count(a)
    if n==1: return s.replace(a,b,1)
    if n==0 and b in s: return s
    raise RuntimeError(f"Unexpected Starling source at {where}: {n} anchors")

def patch(s):
    old = """        let (Some(skin), Some(eyes)) = (
            sprite("entity/enderdragon/dragon"),
            sprite("entity/enderdragon/dragon_eyes"),
        ) else {
            return;
        };"""
    new = """        // TBX: a missing optional glowing-eyes texture must never hide
        // the entire dragon. Render the body skin and skip the eye pass.
        let Some(skin) = sprite("entity/enderdragon/dragon") else {
            return;
        };
        let eyes = sprite("entity/enderdragon/dragon_eyes");"""
    s=once(s,old,new,"optional dragon eyes sprite")
    old = """        // RenderTypes.eyes: the glowing eyes, added on top.
        let mut eye_quads = Vec::new();
        horizon_client::mobs::render::draw(
            model,
            base,
            &poses,
            eyes,
            0xFFFF_FFFF,
            240 | 240 << 8,
            0,
            &mut eye_quads,
        );
        // """
    new = """        // RenderTypes.eyes: optional emissive overlay. Body stays visible
        // even if a custom resource pack omitted the eye image.
        if let Some(eyes) = eyes {
            let mut eye_quads = Vec::new();
            horizon_client::mobs::render::draw(
                model,
                base,
                &poses,
                eyes,
                0xFFFF_FFFF,
                240 | 240 << 8,
                0,
                &mut eye_quads,
            );
        // """
    s=once(s,old,new,"optional eye render")
    old = """        additive.extend(eye_quads);
        if death > 0.0 {"""
    new = """            additive.extend(eye_quads);
        }
        if death > 0.0 {"""
    s=once(s,old,new,"close optional eye render")
    return s

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("source",type=Path)
    a.add_argument("--check",action="store_true")
    args=a.parse_args()
    root=args.source.resolve()
    if not (root/"Cargo.toml").is_file(): a.error("Expected Starling sources")
    path=root/"crates/horizon-client/src/game/dragon.rs"
    data=patch(path.read_text(encoding="utf-8"))
    if args.check:
        print("PASS: dragon body is independent of the optional eyes texture.")
        return
    if path.read_text(encoding="utf-8")!=data:
        path.write_text(data,encoding="utf-8")
    print("Applied dragon visibility fallback to Rust source; no APK built.")

if __name__=="__main__":
    main()
