//! TBX persistent-world wizard: UI and local draft only, NOT an online world.
use super::{Title, WorldOptions, TBX_WORLD_ADDRESS};
use crate::{hud::{HudAtlas, HudBatch}, ui, lang};
use std::{fs, io::Write as _, path::Path};

pub(super) struct PermanentDraft {
    pub name: String,
    pub seed: Option<i64>,
    pub creative: bool,
    pub options: WorldOptions,
    pub address: String,
    pub focus: bool,
    pub message: Option<String>,
}

fn address_ok(value: &str) -> bool {
    (3..=32).contains(&value.len())
        && !value.starts_with('-')
        && !value.ends_with('-')
        && value.bytes().all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == b'-')
}

/// This stores a proposed slug, not a real DNS registration, live server or hosted world.
pub(super) fn save_draft(saves: &Path, draft: &PermanentDraft) -> Result<(), String> {
    if !address_ok(&draft.address) {
        return Err(lang::get_or("tbx.world.address.invalid", "Invalid address"));
    }
    let base = saves.parent().unwrap_or(saves).join("tbx-permanent-drafts");
    fs::create_dir_all(&base).map_err(|e| e.to_string())?;
    let output = base.join(format!("{}.json", draft.address));
    let data = serde_json::to_vec_pretty(&serde_json::json!({
        "format": "tbx-permanent-world-request-v1",
        "requested_address": draft.address,
        "address_reserved": false,
        "is_online": false,
        "hosting_status": "not_configured",
        "account_requirement": "offline_player_requested_not_implemented",
        "name": draft.name,
        "seed": draft.seed,
        "creative": draft.creative,
        "options": draft.options,
        "note": "An always-on remote host is required; this request is local only."
    })).map_err(|e| e.to_string())?;
    let mut file = fs::OpenOptions::new().write(true).create_new(true)
        .open(output).map_err(|e| e.to_string())?;
    file.write_all(&data).map_err(|e| e.to_string())
}

pub(super) fn draw_address(owner: &Title, atlas: &HudAtlas, batch: &mut HudBatch, draft: &PermanentDraft) {
    let (w, h) = (batch.width.ceil(), batch.height.ceil());
    ui::menu_background(batch, atlas, 0.0, 0.0, w, h, false);
    let center = |s: &str| ((w - HudBatch::text_width(atlas, s)) / 2.0).floor();
    let title = lang::get_or("tbx.world.address.title", "Choose an address");
    batch.text(atlas, &title, center(&title), 20.0, u32::MAX, true);
    let label = lang::get_or("tbx.world.address.label", "Desired address (e.g. my-world)");
    batch.text(atlas, &label, center(&label), h / 2.0 - 56.0, u32::MAX, true);
    owner.caret.borrow_mut().draw(
        batch, atlas, (TBX_WORLD_ADDRESS, &draft.address, 32),
        [(w / 2.0).floor() - 100.0, h / 2.0 - 42.0, 200.0, 20.0],
        draft.focus, owner.started,
    );
    for (i, key) in ["tbx.world.address.hint", "tbx.world.address.cloud",
                     "tbx.world.address.noaccount"].iter().enumerate() {
        let line = lang::get(key);
        batch.text(atlas, &line, center(&line),
            h / 2.0 + 3.0 + i as f32 * 12.0, 0xFFCCCCCC, true);
    }
    if let Some(message) = &draft.message {
        batch.text(atlas, message, center(message), h / 2.0 + 48.0, 0xFFFFFF66, true);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn address_is_only_a_safe_requested_slug() {
        assert!(address_ok("meu-mundo"));
        assert!(address_ok("tbx123"));
        for invalid in ["", "ab", "-mundo", "mundo-", "Mundo", "a.b",
                        "../escape", "meu mundo", "ü", "a/b"] {
            assert!(!address_ok(invalid), "{invalid}");
        }
    }
}
