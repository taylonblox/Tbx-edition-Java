#!/usr/bin/env python3
"""TBX smooth-menu source overlay for pinned Starling v0.8.0.

Problem: menus in an active world still render the complete expensive shader
pack and its shadow/post passes, stalling UI/touch input on weak Android GPUs.
Solution: on Android with a selected shader, pause/options render a simplified
menu-only Frame, without world/shader passes. The shader selection and graphics
settings are preserved and normal rendering returns when the screen closes.

A separate touch fix cancels gestures crossing gameplay/menu transitions so
the release of a finger started on the old screen cannot click the new menu.
No render resolution changes; does not compile or create an APK.

The menu background is simplified while active (not a live shader screenshot);
this is an experimental UX trade-off pending actual-device testing.
"""
from __future__ import annotations
import argparse
from pathlib import Path

RENDER_OLD = """        let alpha = self.clock.fraction();
        // Camera.getCameraEntityPartialTicks: the view, the hand and the
        // player's own model stay smooth while the level is frozen."""

RENDER_NEW = """        // TBX: heavy shader packs need not rerender the entire world just to
        // paint the pause/options UI. World render/post/shadow passes remain
        // configured and resume unmodified when the player leaves the menu.
        // A UI-only frame uses the loading/title renderer path, which already
        // skips installed shader passes and avoids costly world geometry.
        // This deliberately sacrifices the *live* world behind these menus
        // rather than lowering gameplay resolution (which stays untouched).
        if cfg!(target_os = "android")
            && self.title.is_none()
            && matches!(self.screen, Screen::Paused | Screen::Options)
            && self.settings.horizon.shader_choice().is_some()
            && self.renderer.as_ref().is_some_and(|r| r.screenshot.is_none())
        {
            let mut hud = horizon_client::spans::time("hud", || self.hud(size));
            self.flush_ime(&mut hud);
            hud.patches.append(&mut self.map_patches);
            if let Some(renderer) = &mut self.renderer {
                let result = renderer.render(&loading_frame(&hud));
                self.frame_drawn = matches!(result, Ok(true));
                return result;
            }
        }
        let alpha = self.clock.fraction();
        // Camera.getCameraEntityPartialTicks: the view, the hand and the
        // player's own model stay smooth while the level is frozen."""

TOUCH_OLD = """        {
            self.android_release_touch_keys(true);
            self.pad.set_touch_state(Default::default());
        }"""

TOUCH_NEW = """        {
            self.android_release_touch_keys(true);
            // TBX: a finger that started touching gameplay must never click a
            // pause/options button on release after the screen transition.
            // Cancel scroll/drag/tap ownership before showing the next menu.
            self.mobile.ui.cancel();
            self.pad.set_touch_state(Default::default());
        }"""

def replace_once(source: str, before: str, after: str, label: str) -> str:
    count = source.count(before)
    if count == 1:
        return source.replace(before, after, 1)
    if count == 0 and source.count(after) == 1:
        return source
    raise RuntimeError(f"{label}: incompatible Starling changes (anchor count={count})")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("starling_source", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.starling_source.resolve()
    if not (root / "Cargo.toml").is_file():
        parser.error("Expected pinned Starling source tree")
    changes = [
        (root / "crates/horizon-client/src/game.rs", RENDER_OLD, RENDER_NEW, "UI-only renderer"),
        (root / "crates/horizon-client/src/game/mobile_controls.rs", TOUCH_OLD, TOUCH_NEW,
         "cancel stale menu touches"),
    ]
    prepared = []
    for path, before, after, label in changes:
        original = path.read_text(encoding="utf-8")
        prepared.append((path, original, replace_once(original, before, after, label)))
    if args.check:
        print("PASS: Starling v0.8.0 smooth shader menu and touch transition anchors")
        print("Would update:", ", ".join(str(p.relative_to(root)) for p, a, b in prepared if a != b) or "none")
        return
    for path, old, new in prepared:
        if old != new:
            path.write_text(new, encoding="utf-8")
    print("TBX menu-only shader bypass and touch transition guard applied to source.")
    print("Game resolution untouched. No APK generated. Still needs Android build/device testing.")

if __name__ == "__main__":
    main()
