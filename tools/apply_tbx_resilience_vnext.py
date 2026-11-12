#!/usr/bin/env python3
"""Apply TBX weekly world backups and automatic shader recovery source changes."""
import argparse
from pathlib import Path

def once(s, before, after, what):
    n = s.count(before)
    if n == 1: return s.replace(before, after, 1)
    if n == 0 and after in s: return s
    raise RuntimeError(f"{what}: incompatible Starling source (count={n})")

def title(s):
    s = once(s, "mod create_world;",
        "mod create_world;\nmod tbx_backup;", "module")
    s = once(s, "    reopen_data_packs: bool,\n}",
        "    reopen_data_packs: bool,\n"
        "    tbx_auto_backup_resume: bool,\n"
        "    tbx_auto_backup_running: bool,\n}", "state")
    s = once(s, "            reopen_data_packs: false,\n",
        "            reopen_data_packs: false,\n"
        "            tbx_auto_backup_resume: false,\n"
        "            tbx_auto_backup_running: false,\n", "defaults")
    before = """            if let Some(stem_asked) = self.backup_then_open.take()
                && let Action::Play { folder } = self.after_prompt(world.clone(), stem_asked)
            {
                self.open_request = Some(folder);
            }"""
    after = """            // TBX: a completed copy is marked only when the ZIP succeeded.
            // Skip a second backup in this launch (even if the ZIP failed).
            if std::mem::take(&mut self.tbx_auto_backup_running) {
                self.tbx_auto_backup_resume = true;
                if result.is_ok() {
                    tbx_backup::mark_success(&self.saves.join(&world.folder));
                }
            }
            if let Some(stem_asked) = self.backup_then_open.take()
                && let Action::Play { folder } = self.after_prompt(world.clone(), stem_asked)
            {
                self.open_request = Some(folder);
            }"""
    s = once(s, before, after, "backups finish")
    before = """        if crate::save::low_disk_space(&dir) {
            self.mode = Mode::LowDiskSpace { world };
            return Action::None;
        }
        Action::Play {
            folder: world.folder,
        }"""
    after = """        if crate::save::low_disk_space(&dir) {
            self.mode = Mode::LowDiskSpace { world };
            return Action::None;
        }
        // TBX: first safe launch and once every seven days on Android.
        // Uses the EXISTING background ZIP worker and progress display;
        // no compression work on the render thread, no world deletions.
        let resuming = std::mem::take(&mut self.tbx_auto_backup_resume);
        if cfg!(target_os = "android") && !resuming && tbx_backup::due(&dir) {
            self.tbx_auto_backup_running = true;
            self.backup_then_open = Some(true);
            self.start_backup(world);
            return Action::None;
        }
        Action::Play {
            folder: world.folder,
        }"""
    s = once(s, before, after, "safe world start")
    return s

def shader(s):
    before = """    fn shader_pack_failed(&mut self, name: &str, dimension: i32, error: &str) {
        log::error!("shader pack {name}: turned off: {error}");"""
    after = """    fn shader_pack_failed(&mut self, name: &str, dimension: i32, error: &str) {
        log::error!("shader pack {name}: turned off: {error}");
        self.tbx_record_shader_recovery(name, error);"""
    s = once(s, before, after, "shader crash")
    before = """        let name = std::mem::take(&mut self.settings.horizon.shader_pack);
        log::error!("shader pack {name}: turned off after the graphics device was lost");"""
    after = """        let name = std::mem::take(&mut self.settings.horizon.shader_pack);
        log::error!("shader pack {name}: turned off after the graphics device was lost");
        self.tbx_record_shader_recovery(&name, "graphics device lost");"""
    s = once(s, before, after, "device lost")
    before = """    /// Turns off the pack """
    # The module is inserted before the existing recovery handler. The
    # command uses an exact Rust method signature instead of generic text.
    before = """    fn shader_pack_failed(&mut self, name: &str, dimension: i32, error: &str) {"""
    extra = """    fn tbx_record_shader_recovery(&self, name: &str, reason: &str) {
        let safe_name = name.replace('\\n', " ").replace('\\r', " ");
        let note = format!("TBX shader recovery\\npack: {safe_name}\\nreason: {reason}\\n");
        let path = Self::game_dir().join("tbx-last-shader-recovery.txt");
        if let Err(e) = std::fs::write(path, note) {
            log::warn!("TBX: recovery note could not be saved: {e}");
        }
    }

    fn shader_pack_failed(&mut self, name: &str, dimension: i32, error: &str) {"""
    s = once(s, before, extra, "shader recovery note helper")
    return s

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--rust-module", type=Path, required=True)
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    root = a.source.resolve()
    if not (root / "Cargo.toml").is_file(): p.error("Expected Starling checkout")
    paths = {
        "crates/horizon-client/src/title.rs": title,
        "crates/horizon-client/src/game/shader_packs.rs": shader,
    }
    patch = {root / rel: fn((root / rel).read_text(encoding="utf-8"))
             for rel, fn in paths.items()}
    dst = root / "crates/horizon-client/src/title/tbx_backup.rs"
    backup = a.rust_module.read_text(encoding="utf-8")
    if dst.exists() and dst.read_text(encoding="utf-8") != backup:
        raise RuntimeError("A different backup module already exists")
    patch[dst] = backup
    if a.check:
        print("PASS: automatic weekly backups and shader safe-start recovery notes")
        return
    for path, value in patch.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != value:
            path.write_text(value, encoding="utf-8")
    print("TBX safety source patches applied, no APK built.")

if __name__ == "__main__":
    main()
