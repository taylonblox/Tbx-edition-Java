//! TBX: native ZIP backup scheduling, no world deletion or cloud calls.
use std::{fs, path::Path, time::{Duration, SystemTime}};
const INTERVAL: Duration = Duration::from_secs(7 * 24 * 3600);
const MARK: &str = ".tbx-last-automatic-backup";

pub(super) fn due(dir: &Path) -> bool {
    let Ok(modified) = fs::metadata(dir.join(MARK)).and_then(|m| m.modified()) else {
        return true;
    };
    SystemTime::now()
        .duration_since(modified)
        .map_or(false, |elapsed| elapsed >= INTERVAL)
}

pub(super) fn mark_success(dir: &Path) {
    if let Err(e) = fs::write(dir.join(MARK), b"TBX successful automatic backup\n") {
        log::warn!("TBX: could not record world backup success: {e}");
    }
}

#[cfg(test)]
mod tbx_tests {
    use super::*;
    #[test]
    fn a_new_world_gets_one_backup_then_waits_seven_days() {
        let dir = std::env::temp_dir().join(format!(
            "tbx-backup-{}-{:?}", std::process::id(),
            std::thread::current().id()));
        fs::create_dir_all(&dir).unwrap();
        let _ = fs::remove_file(dir.join(MARK));
        assert!(due(&dir));
        mark_success(&dir);
        assert!(!due(&dir));
        fs::remove_dir_all(dir).unwrap();
    }
}
