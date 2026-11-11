#!/usr/bin/env python3
"""Add a client-only permanent-world wizard to pinned Starling 0.8.0 source.

Reuses Minecraft Java world-creation options and widgets. No APK/cloud world,
online account, real hostname or server process is created by this patch.
"""
import argparse
import json
from pathlib import Path

TITLE = "crates/horizon-client/src/title.rs"
EN = "crates/horizon-client/assets/horizon/lang/en_us.json"
PT = "crates/horizon-client/assets/horizon/lang/pt_br.json"
RUST = "crates/horizon-client/src/title/tbx_permanent_world.rs"
LANG = {
    "tbx.world.create": ("Create permanent world", "Criar mundo permanente"),
    "tbx.world.address.title": ("Choose an address", "Escolha o endereço"),
    "tbx.world.address.label": ("Desired address (e.g. my-world)", "Endereço desejado (ex.: meu-mundo)"),
    "tbx.world.address.hint": (
        "This is a draft. The address is not reserved or online.",
        "Isso é um rascunho. O endereço não está reservado nem online."),
    "tbx.world.address.cloud": (
        "24/7 access needs cloud hosting, which is not yet connected.",
        "Acesso 24h precisa de hospedagem na nuvem, ainda não conectada."),
    "tbx.world.address.noaccount": (
        "No Microsoft account is planned for this world.",
        "Não planejamos exigir conta Microsoft nesse mundo."),
    "tbx.world.address.save": ("Save world draft", "Salvar rascunho do mundo"),
    "tbx.world.address.back": ("Back to world options", "Voltar às opções do mundo"),
    "tbx.world.address.invalid": (
        "Use 3–32 lowercase letters, digits or hyphens, not at the start or end.",
        "Use 3 a 32 letras minúsculas, números ou hífens, sem hífen no início ou fim."),
    "tbx.world.address.saved": (
        "Draft saved locally. It is not online yet.",
        "Rascunho salvo no celular. O mundo ainda não está online."),
    "tbx.world.address.failed": ("Could not save the draft", "Não foi possível salvar o rascunho"),
}

def one(text, before, after, name):
    found = text.count(before)
    if found == 1:
        return text.replace(before, after, 1)
    if found == 0 and after in text:
        return text
    raise ValueError(f"{name}: incompatible upstream source ({found} anchors)")

def patch_title(s):
    edits = [
        ("mod create_world;", "mod create_world;\nmod tbx_permanent_world;", "module"),
        ("    reopen_data_packs: bool,\n}",
         "    reopen_data_packs: bool,\n"
         "    tbx_permanent: bool,\n"
         "    tbx_address: Option<tbx_permanent_world::PermanentDraft>,\n}", "fields"),
        ("            reopen_data_packs: false,\n",
         "            reopen_data_packs: false,\n"
         "            tbx_permanent: false,\n"
         "            tbx_address: None,\n", "initialize"),
        ("    fn cancel_create(&mut self) {\n",
         "    fn cancel_create(&mut self) {\n"
         "        if self.tbx_permanent {\n"
         "            self.tbx_permanent = false;\n"
         "            self.tbx_address = None;\n"
         "            self.mode = Mode::Multiplayer(crate::multiplayer::Screen::list(&self.saves));\n"
         "            return;\n"
         "        }\n", "back to multiplayer"),
        ("            trailing: None,\n        };\n        match &self.mode {\n            Mode::Main => {",
         "            trailing: None,\n        };\n"
         "        if self.tbx_address.is_some() {\n"
         "            return vec![\n"
         "                b((w - 308.0) / 2.0, h - 29.0, 150.0,\n"
         "                    &lang::get_or(\"tbx.world.address.save\", \"Save world draft\"), true, 240),\n"
         "                b((w - 308.0) / 2.0 + 158.0, h - 29.0, 150.0,\n"
         "                    &lang::get_or(\"tbx.world.address.back\", \"Back to world options\"), true, 241),\n"
         "            ];\n"
         "        }\n"
         "        match &self.mode {\n            Mode::Main => {", "address buttons"),
        ("            Mode::Create {\n                creative, options, ..\n"
         "            } => create_world::buttons(w, h, *creative, options),",
         "            Mode::Create {\n                creative, options, ..\n"
         "            } => {\n"
         "                let mut buttons = create_world::buttons(w, h, *creative, options);\n"
         "                if self.tbx_permanent {\n"
         "                    if let Some(create) = buttons.iter_mut().find(|b| b.id == 21) {\n"
         "                        create.label = lang::get_or(\"tbx.world.create\", \"Create permanent world\");\n"
         "                    }\n"
         "                }\n"
         "                buttons\n            },", "same world buttons"),
        ("            Mode::Multiplayer(screen) => screen\n"
         "                .buttons(w, h)\n"
         "                .into_iter()\n"
         "                .map(|(x, y, bw, label, enabled, id)| b(x, y, bw, &label, enabled, id))\n"
         "                .collect(),",
         "            Mode::Multiplayer(screen) => {\n"
         "                let mut buttons: Vec<_> = screen.buttons(w, h).into_iter()\n"
         "                    .map(|(x, y, bw, label, enabled, id)|\n"
         "                        b(x, y, bw, &label, enabled, id)).collect();\n"
         "                if matches!(screen, crate::multiplayer::Screen::List { .. }) {\n"
         "                    buttons.push(b((w - 29.0).max(0.0), 6.0, 20.0, \"+\", true, 239));\n"
         "                }\n"
         "                buttons\n            },", "plus widget"),
        ("        match &self.mode {\n            Mode::Main => {}\n            Mode::Create {\n"
         "                creative, options, ..\n"
         "            } => return create_world::button_narration(b, *creative, options),",
         "        if self.tbx_address.is_some() {\n"
         "            return Narratable::button(b.label.clone(), rect, b.enabled);\n"
         "        }\n"
         "        if b.id == 239 {\n"
         "            return Narratable::button(\n"
         "                lang::get_or(\"tbx.world.create\", \"Create permanent world\"), rect, b.enabled);\n"
         "        }\n"
         "        match &self.mode {\n            Mode::Main => {}\n"
         "            Mode::Create {\n                creative, options, ..\n"
         "            } => return create_world::button_narration(b, *creative, options),", "narration"),
        ("        match &self.mode {\n            Mode::Main => {\n                draw_logo(atlas, batch, w);",
         "        if let Some(draft) = self.tbx_address.as_ref() {\n"
         "            tbx_permanent_world::draw_address(self, atlas, batch, draft);\n"
         "        } else {\n"
         "        match &self.mode {\n            Mode::Main => {\n                draw_logo(atlas, batch, w);", "address drawing begin"),
        ("            Mode::Multiplayer(screen) => screen.draw(\n"
         "                atlas,\n                batch,\n                &mut self.caret.borrow_mut(),\n"
         "                self.started,\n                cursor,\n                hide_server_address,\n"
         "            ),\n        }\n        for b in self.buttons(w, h) {",
         "            Mode::Multiplayer(screen) => screen.draw(\n"
         "                atlas,\n                batch,\n                &mut self.caret.borrow_mut(),\n"
         "                self.started,\n                cursor,\n                hide_server_address,\n"
         "            ),\n        }\n        }\n        for b in self.buttons(w, h) {", "address drawing end"),
        ("    fn click_action(&mut self, x: f32, y: f32, (w, h): (f32, f32), hit: Option<u8>) -> Action {\n"
         "        match (&mut self.mode, hit) {",
         "    fn click_action(&mut self, x: f32, y: f32, (w, h): (f32, f32), hit: Option<u8>) -> Action {\n"
         "        if hit == Some(239) && matches!(self.mode,\n"
         "            Mode::Multiplayer(crate::multiplayer::Screen::List { .. })) {\n"
         "            self.tbx_permanent = true;\n"
         "            self.tbx_address = None;\n"
         "            self.focused_button = None;\n"
         "            self.mode = Self::new_world();\n"
         "            return Action::None;\n"
         "        }\n"
         "        if hit == Some(241) && self.tbx_address.is_some() {\n"
         "            self.tbx_address = None;\n"
         "            self.focused_button = None;\n"
         "            return Action::None;\n"
         "        }\n"
         "        if let Some(draft) = self.tbx_address.as_mut() {\n"
         "            match hit {\n"
         "                Some(240) => {\n"
         "                    let result = tbx_permanent_world::save_draft(&self.saves, draft);\n"
         "                    draft.message = Some(match result {\n"
         "                        Ok(()) => lang::get_or(\"tbx.world.address.saved\",\n"
         "                            \"Draft saved locally. It is not online yet.\"),\n"
         "                        Err(e) => format!(\"{}: {e}\", lang::get_or(\n"
         "                            \"tbx.world.address.failed\", \"Could not save the draft\")),\n"
         "                    });\n"
         "                }\n"
         "                None => {\n"
         "                    draft.focus = (w / 2.0 - 100.0..w / 2.0 + 100.0).contains(&x)\n"
         "                        && (h / 2.0 - 42.0..h / 2.0 - 22.0).contains(&y);\n"
         "                }\n"
         "                _ => {}\n"
         "            }\n"
         "            return Action::None;\n"
         "        }\n"
         "        if self.tbx_permanent && hit == Some(21)\n"
         "            && matches!(self.mode, Mode::Create { .. }) {\n"
         "            if let Action::Create { name, seed, creative, options, .. } = self.create_action() {\n"
         "                self.tbx_address = Some(tbx_permanent_world::PermanentDraft {\n"
         "                    name, seed, creative, options,\n"
         "                    address: String::new(), focus: true, message: None,\n"
         "                });\n"
         "                self.focused_button = None;\n"
         "            }\n"
         "            return Action::None;\n"
         "        }\n"
         "        match (&mut self.mode, hit) {", "handle wizard"),
        ("    pub fn focused_field(&mut self) -> Option<(crate::clipboard::FieldId, &mut String, usize)> {\n"
         "        if self.rules.get_mut().is_some() {",
         "    pub fn focused_field(&mut self) -> Option<(crate::clipboard::FieldId, &mut String, usize)> {\n"
         "        if let Some(draft) = self.tbx_address.as_mut() {\n"
         "            return draft.focus.then_some((TBX_WORLD_ADDRESS, &mut draft.address, 32));\n"
         "        }\n        if self.rules.get_mut().is_some() {", "focus address"),
        ("    pub fn has_caret_field(&mut self) -> bool {\n"
         "        // The game rules' boxes edit themselves",
         "    pub fn has_caret_field(&mut self) -> bool {\n"
         "        if let Some(draft) = self.tbx_address.as_ref() { return draft.focus; }\n"
         "        // The game rules' boxes edit themselves", "caret address"),
        ("    fn edit_field(&mut self, f: impl FnOnce(&mut crate::ui::EditBox)) -> bool {\n"
         "        if let Some(rules) = self.rules.get_mut() {",
         "    fn edit_field(&mut self, f: impl FnOnce(&mut crate::ui::EditBox)) -> bool {\n"
         "        if let Some(draft) = self.tbx_address.as_mut() {\n"
         "            if !draft.focus { return false; }\n"
         "            self.caret.get_mut().edit(TBX_WORLD_ADDRESS, &mut draft.address, 32, f);\n"
         "            draft.message = None;\n"
         "            return true;\n"
         "        }\n        if let Some(rules) = self.rules.get_mut() {", "typing"),
        ("    fn focused_rect(&self, (w, h): (f32, f32)) -> Option<[f32; 4]> {\n"
         "        let x = (w / 2.0).floor() - 100.0;",
         "    fn focused_rect(&self, (w, h): (f32, f32)) -> Option<[f32; 4]> {\n"
         "        if let Some(draft) = self.tbx_address.as_ref() {\n"
         "            return draft.focus.then_some([(w / 2.0).floor() - 100.0,\n"
         "                h / 2.0 - 42.0, 200.0, 20.0]);\n"
         "        }\n        let x = (w / 2.0).floor() - 100.0;", "text field bounds"),
        ("    pub fn confirm_key_size(&mut self, size: (f32, f32)) -> (Action, bool) {\n"
         "        self.remember_direct_address();",
         "    pub fn confirm_key_size(&mut self, size: (f32, f32)) -> (Action, bool) {\n"
         "        if self.tbx_address.is_some() && self.focused_button.is_none() {\n"
         "            return (self.click_action(0.0, 0.0, size, Some(240)), true);\n"
         "        }\n"
         "        if self.tbx_permanent && self.tbx_address.is_none()\n"
         "            && matches!(self.mode, Mode::Create { .. }) && self.focused_button.is_none() {\n"
         "            return (self.click_action(0.0, 0.0, size, Some(21)), true);\n"
         "        }\n"
         "        self.remember_direct_address();", "enter key"),
        ("    pub fn escape(&mut self) {\n"
         "        // GenericMessageScreen.shouldCloseOnEsc is false:",
         "    pub fn escape(&mut self) {\n"
         "        if self.tbx_address.take().is_some() {\n"
         "            self.focused_button = None;\n"
         "            return;\n"
         "        }\n"
         "        // GenericMessageScreen.shouldCloseOnEsc is false:", "back key"),
        ("const WORLD_SEED: crate::clipboard::FieldId = (\"world.seed\", 0);",
         "const WORLD_SEED: crate::clipboard::FieldId = (\"world.seed\", 0);\n"
         "const TBX_WORLD_ADDRESS: crate::clipboard::FieldId = (\"tbx.permanent.requested-address\", 0);",
         "field key"),
    ]
    for before, after, description in edits:
        s = one(s, before, after, description)
    return s

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("starling_source", type=Path)
    cli.add_argument("--check", action="store_true")
    cli.add_argument("--rust-module", type=Path,
                     help="Path to tools/tbx_permanent_world.rs (required)")
    a = cli.parse_args()
    root = a.starling_source.resolve()
    if not (root / "Cargo.toml").is_file():
        cli.error("Expected Starling source")
    if a.rust_module is None or not a.rust_module.is_file():
        cli.error("Provide --rust-module path to TBX Rust helper")
    rust = a.rust_module.read_text(encoding="utf-8")
    target = patch_title((root / TITLE).read_text(encoding="utf-8"))
    staged = {root / TITLE: target, root / RUST: rust}
    for path, language in ((EN, 0), (PT, 1)):
        original = json.loads((root / path).read_text(encoding="utf-8"))
        for key, translation in LANG.items():
            if key in original and original[key] != translation[language]:
                raise RuntimeError("Refusing to replace upstream translation: " + key)
            original[key] = translation[language]
        staged[root / path] = json.dumps(original, ensure_ascii=False, indent=2) + "\n"
    if (root / RUST).exists() and (root / RUST).read_text(encoding="utf-8") != rust:
        raise ValueError("Rust module already exists with different content")
    if a.check:
        print("PASS: multiplayer plus, vanilla world creation reuse, choose address draft")
        return
    for file, data in staged.items():
        file.parent.mkdir(parents=True, exist_ok=True)
        if not file.exists() or file.read_text(encoding="utf-8") != data:
            file.write_text(data, encoding="utf-8")
    print("Applied TBX world wizard to source. No APK, no 24h hosting, no DNS.")

if __name__ == "__main__":
    main()
