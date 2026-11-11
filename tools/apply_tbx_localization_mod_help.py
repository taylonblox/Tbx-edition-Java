#!/usr/bin/env python3
"""Source-only TBX localization and mod guidance overlay for Starling 0.8.0.

Does not build an APK or claim automatic conversion from Java bytecode to Rust.
Runs after apply_starling_tbx_ui.py on the pinned Starling 0.8.0 source tree.
--check validates all anchors and payloads without modifying files.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

EN = {
    "tbx.mods.guide.native": "Native mod (.hnmod): select the mods, then tap Compile. This builds a separate game containing those mods; it does not convert Java.",
    "tbx.mods.guide.jar": "Java mod (.jar): it cannot run directly. The TBX port assistant can inspect it and recover data/assets, but its Java code must be adapted and tested in Rust.",
    "tbx.mods.guide.warning": "Never trust a mod file without knowing its source. A completed compilation does not prove that the mod works.",
    "tbx.diagnostics.notice.raw": "Technical logs and original error codes remain unchanged inside the exported ZIP so developers can diagnose problems.",
    "tbx.diagnostics.summary.previous": "No completion record for the previous session; last phase: %s. Android may stop background apps without a completion record. This alone does not indicate a crash.",
    "tbx.diagnostics.summary.export": "Export a diagnostic ZIP to send with your report. It includes local logs, Android exit history and saved performance recordings. Review before sharing.",
    "tbx.mods.port.scan": "Analyze Java mod",
    "tbx.mods.port.prepare": "Prepare Rust port (source only)",
    "tbx.mods.port.not_automatic": "This is an initial port plan, not a compiled or playable mod.",
}
PT = {
    "tbx.mods.guide.native": "Mod nativo (.hnmod): selecione os mods e toque em Compilar. Isso cria uma versão separada do jogo com esses mods; não converte Java.",
    "tbx.mods.guide.jar": "Mod Java (.jar): ele não funciona diretamente. O assistente TBX pode analisar o arquivo e recuperar dados e recursos, mas o código Java precisa ser adaptado e testado em Rust.",
    "tbx.mods.guide.warning": "Só use mods de fontes confiáveis. Compilar sem erros não garante que o mod funcione.",
    "tbx.diagnostics.notice.raw": "Os registros técnicos e códigos de erro originais continuam intactos no ZIP exportado, para permitir a investigação de falhas.",
    "tbx.diagnostics.summary.previous": "Não há registro de conclusão da sessão anterior; última etapa: %s. O Android pode encerrar aplicativos em segundo plano sem esse registro. Isso, por si só, não significa que o jogo travou.",
    "tbx.diagnostics.summary.export": "Exporte um ZIP de diagnóstico para enviar com o relatório. Ele inclui registros locais, histórico de encerramentos do Android e gravações de desempenho. Revise antes de compartilhar.",
    "tbx.mods.port.scan": "Analisar mod Java",
    "tbx.mods.port.prepare": "Preparar adaptação para Rust (somente código)",
    "tbx.mods.port.not_automatic": "Este é um plano inicial de adaptação, não um mod compilado ou jogável.",
}

def one(text: str, old: str, new: str, name: str) -> str:
    found = text.count(old)
    if found == 1:
        return text.replace(old, new, 1)
    if found == 0 and new in text:
        return text
    raise RuntimeError(f"{name}: upstream changed unexpectedly (found {found})")

def diagnostics(text: str) -> str:
    old = '''    match previous {
        Some(v) if v["clean_exit"] != true => format!("No completion record for the previous session; last phase: {}. Android may stop background apps without a completion record. This alone does not indicate a crash.", v["phase"].as_str().unwrap_or("unknown")),
        _ => "Export one diagnostic ZIP to send with your report. It includes local logs, Android exit history and retained performance recordings. Review before sharing.".into(),
    }'''
    new = '''    // TBX: resolve the summary through the same language dictionary used
    // by the Minecraft options menu. Technical logs are never translated.
    match previous {
        Some(v) if v["clean_exit"] != true => {
            let phase = v["phase"].as_str().unwrap_or("unknown");
            crate::lang::get("tbx.diagnostics.summary.previous").replacen("%s", phase, 1)
        }
        _ => crate::lang::get("tbx.diagnostics.summary.export"),
    }'''
    return one(text, old, new, "diagnostics::summary")

def menu(text: str) -> str:
    old = '''                    Row::Note(lang::get("starling.diagnostics.overhead")),
                    Row::Buttons('''
    new = '''                    Row::Note(lang::get("starling.diagnostics.overhead")),
                    Row::Note(lang::get("tbx.diagnostics.notice.raw")),
                    Row::Buttons('''
    text = one(text, old, new, "diagnostic notice")
    old = '''            Page::Mods => {
                // Android: which game runs, above the mods.
                let mut rows = native_game_rows(s);
                if s.mods.installed.is_empty() {'''
    new = '''            Page::Mods => {
                // TBX: explain the existing native-mod Compile button without
                // claiming .jar bytecode can be turned into Rust automatically.
                // lang::get follows the Minecraft language selected in Options.
                let mut rows = native_game_rows(s);
                if cfg!(target_os = "android") {
                    rows.push(Row::Note(lang::get("tbx.mods.guide.native")));
                    rows.push(Row::Note(lang::get("tbx.mods.guide.jar")));
                    rows.push(Row::Note(lang::get("tbx.mods.guide.warning")));
                }
                if s.mods.installed.is_empty() {'''
    return one(text, old, new, "mod guidance")

TRANSFORMS = {
    "crates/horizon-client/src/diagnostics.rs": diagnostics,
    "crates/horizon-client-render/src/options_ui.rs": menu,
}
LANG = {
    "crates/horizon-client/assets/horizon/lang/en_us.json": EN,
    "crates/horizon-client/assets/horizon/lang/pt_br.json": PT,
}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("starling_source", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = args.starling_source.resolve()
    if not (root / "Cargo.toml").is_file():
        ap.error("expected an extracted Starling Rust source checkout")

    targets = {}
    for relative, edit in TRANSFORMS.items():
        p = root / relative
        targets[p] = edit(p.read_text(encoding="utf-8"))
    for relative, translations in LANG.items():
        p = root / relative
        original = json.loads(p.read_text(encoding="utf-8"))
        for key, value in translations.items():
            existing = original.get(key)
            if existing is not None and existing != value:
                raise RuntimeError(f"Refusing to overwrite upstream translation {key}")
            original[key] = value
        targets[p] = json.dumps(original, ensure_ascii=False, indent=2) + "\n"
    if not args.check:
        for p, data in targets.items():
            if p.read_text(encoding="utf-8") != data:
                p.write_text(data, encoding="utf-8")
        print("TBX source localized: dynamic pt_br/en_us diagnostics + native mod help.")
    else:
        print("PASS: localization and mod help patch compatible with pinned Starling source.")
    print("No APK was built. Raw diagnostic log messages remain untouched.")

if __name__ == "__main__":
    main()
