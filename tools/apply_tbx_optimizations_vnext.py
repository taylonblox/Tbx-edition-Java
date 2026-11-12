#!/usr/bin/env python3
"""TBX next-version performance and touch safety for pinned Starling 0.8.0.

Source-only. No APK. Does not change Minecraft render resolution. Keeps water
and sun-dependent shader lighting available, caps only expensive shadow work
in Auto profile on modest phones, spreads terrain uploads across frames and
prevents very stale Android menu finger-ups from activating buttons.
"""
from __future__ import annotations
import argparse
from pathlib import Path

RENDER = "crates/horizon-client/src/game.rs"
SHADERS = "crates/horizon-client/src/game/shader_packs.rs"
TOUCH = "crates/horizon-client/src/android_control_ui.rs"

def once(s: str, original: str, replacement: str, name: str) -> str:
    found = s.count(original)
    if found == 1:
        return s.replace(original, replacement, 1)
    if found == 0 and replacement in s:
        return s
    raise RuntimeError(f"Starling 0.8.0 changed {name} (anchor count {found}); refusing a blind patch")

def shader(s: str) -> str:
    s = once(s,
        "match Tier::here().unwrap_or(Tier::High) {",
        "match Tier::here().unwrap_or(if cfg!(target_os = \"android\") { Tier::Low } else { Tier::High }) {",
        "safe fallback for unknown Android GPU")
    s = once(s,
        """            Tier::Mid => Self {
                rank: 0,
                shadow_resolution: 1024.0,
                shadow_distance: 64.0,
            },
            Tier::Low => Self {
                rank: 0,
                shadow_resolution: 512.0,
                shadow_distance: 64.0,
            },""",
        """            Tier::Mid => Self {
                rank: 0,
                shadow_resolution: 768.0,
                shadow_distance: 56.0,
            },
            Tier::Low => Self {
                rank: 0,
                shadow_resolution: 512.0,
                shadow_distance: 48.0,
            },""",
        "Auto shader shadow cost on older GPUs")
    start = s.index("    pub(super) fn world_scale(&self) -> f32 {")
    stop = s.index("\n    /// The Shader Options page opened:", start)
    old = s[start:stop]
    new = """    pub(super) fn world_scale(&self) -> f32 {
        // TBX: don't silently blur the game when Auto shaders are selected.
        // Shadow/profile budgets above control expensive GPU passes instead.
        // The resolution slider remains exclusively the player's decision.
        self.settings.horizon.resolution_scale as f32 / 100.0
    }
"""
    return once(s, old, new, "player-owned render resolution")

def render(s: str) -> str:
    return once(s,
        """            if !budgeted && self.pending_uploads.is_empty() && uploads.len() <= AUTO_UPLOADS_AT_ONCE
            {""",
        """            // TBX Android: even a small burst of large meshes can block
            // the UI thread for a full frame on a low-memory phone. Always
            // go through the existing nearest-first time-budgeted path here.
            if !cfg!(target_os = "android")
                && !budgeted && self.pending_uploads.is_empty()
                && uploads.len() <= AUTO_UPLOADS_AT_ONCE
            {""",
        "spread terrain uploads on Android")

def touch(s: str) -> str:
    s = once(s, """    gesture: Option<(u64, [f32; 2], [f32; 2], bool)>,
    pointer_drag: Option<u64>,""",
         """    gesture: Option<(u64, [f32; 2], [f32; 2], bool)>,
    /// The first time the GUI finger landed: a delayed release must never
    /// activate another menu widget after the GPU froze for seconds.
    tbx_gesture_started: Option<Instant>,
    pointer_drag: Option<u64>,""", "gesture timestamp field")
    s = once(s, """            gesture: None,
            pointer_drag: None,""",
         """            gesture: None,
            tbx_gesture_started: None,
            pointer_drag: None,""", "gesture timestamp default")
    s = once(s, """    pub fn cancel(&mut self) {
        self.gesture = None;
        self.pointer_drag = None;""",
         """    pub fn cancel(&mut self) {
        self.gesture = None;
        self.tbx_gesture_started = None;
        self.pointer_drag = None;""", "gesture timestamp cancel")
    s = once(s, """            if self.gesture.is_none() {
                self.gesture = Some((id, p, p, false));
            }
            return Gesture::None;""",
         """            if self.gesture.is_none() {
                self.gesture = Some((id, p, p, false));
                self.tbx_gesture_started = Some(Instant::now());
            }
            return Gesture::None;""", "record finger down")
    s = once(s, """        if phase == TouchPhase::Ended {
            let tap = !*dragged;
            self.cancel();
            return if tap { Gesture::Tap } else { Gesture::None };
        }""",
         """        if phase == TouchPhase::Ended {
            // TBX: reject a stale click (the GPU or OS may have held input
            // events until a shader-heavy frame completed). Ordinary quick
            // taps still trigger immediately. This doesn't affect scrolling.
            let tap = !*dragged
                && self.tbx_gesture_started.is_some_and(|t|
                    t.elapsed() <= Duration::from_millis(1500));
            self.cancel();
            return if tap { Gesture::Tap } else { Gesture::None };
        }""", "ignore stale touch-up click")
    return s

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("starling_source", type=Path)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    root = args.starling_source.resolve()
    if not (root / "Cargo.toml").is_file():
        p.error("Expected Starling checkout")
    edits = {SHADERS: shader, RENDER: render, TOUCH: touch}
    result = {}
    for rel, fn in edits.items():
        path = root / rel
        result[path] = fn(path.read_text(encoding="utf-8"))
    if args.check:
        print("PASS: shader auto-shadow, unchanged resolution, upload budget, stale tap guard")
        return
    for path, body in result.items():
        if path.read_text(encoding="utf-8") != body:
            path.write_text(body, encoding="utf-8")
    print("TBX optimization sources updated. No APK. Android build/benchmarks still required.")

if __name__ == "__main__":
    main()
