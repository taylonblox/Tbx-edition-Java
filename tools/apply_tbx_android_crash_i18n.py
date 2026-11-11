#!/usr/bin/env python3
"""TBX source-only Android crash/diagnostic localization for Starling 0.8.0.

Adds a game-language reader, pt-BR Android strings, and updates the recovery
activity to explicitly use the game's selected locale (not phone locale).
Never builds an APK; no original error details are translated or discarded.
"""
import argparse
from pathlib import Path

HELPER = r'''package io.github.juanluci.starling;

import android.content.Context;
import android.content.res.Configuration;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** A recovery activity can run while the native renderer is broken.
 * Read only the saved language preference; never load the game to translate.
 */
final class TbxLanguage {
    private TbxLanguage() {}

    private static String readOption(File file) {
        if (file == null || !file.isFile() || file.length() > 1024 * 1024) return null;
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("lang:")) {
                    String value = line.substring(5).trim().toLowerCase(Locale.ROOT);
                    if (value.matches("[a-z]{2,3}[_-][a-z]{2,4}")) return value;
                }
            }
        } catch (java.io.IOException ignored) {
            // The app remains recoverable even if its options are corrupt.
        }
        return null;
    }

    private static String selected(Context context) {
        String shared = StarlingActivity.sharedFolder(context);
        File[] roots = {
            context.getFilesDir(),
            new File(context.getFilesDir(), "game"),
            new File(context.getFilesDir(), "minecraft"),
            shared == null ? null : new File(shared),
            shared == null ? null : new File(shared, "game"),
            shared == null ? null : new File(shared, "minecraft"),
        };
        File selected = null;
        for (File root : roots) {
            if (root == null) continue;
            File option = new File(root, "options.txt");
            if (option.isFile() && (selected == null
                    || option.lastModified() > selected.lastModified())) selected = option;
        }
        String lang = readOption(selected);
        return lang == null ? "en_us" : lang;
    }

    static Locale locale(Context context) {
        // The first localized recovery UI is pt-BR; everything else retains
        // English fallback until a matching translation is available.
        return selected(context).startsWith("pt") ? new Locale("pt", "BR") : Locale.US;
    }

    static String text(Context context, int resId) {
        Configuration c = new Configuration(context.getResources().getConfiguration());
        c.setLocale(locale(context));
        return context.createConfigurationContext(c).getString(resId);
    }

    static String format(Context context, int resId, Object... args) {
        Locale locale = locale(context);
        return String.format(locale, text(context, resId), args);
    }
}
''';

PT = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="diagnostics_title">Diagnóstico</string>
    <string name="diagnostics_intro">Veja os registros e exporte um relatório, mesmo se o jogo não conseguir iniciar.</string>
    <string name="diagnostics_recovery_intro">O jogo não terminou de iniciar na última vez. Tente novamente ou exporte um relatório para investigar o problema.</string>
    <string name="diagnostics_view_log">Ver último registro</string>
    <string name="diagnostics_export">Exportar ZIP de diagnóstico</string>
    <string name="diagnostics_share">Compartilhar último ZIP</string>
    <string name="diagnostics_start">Tentar iniciar o jogo</string>
    <string name="diagnostics_working">Preparando relatório…</string>
    <string name="diagnostics_exported">Relatório exportado. Revise antes de compartilhar.</string>
    <string name="diagnostics_failed">Falha no diagnóstico: %1$s</string>
    <string name="diagnostics_no_report">Exporte um relatório primeiro.</string>
    <string name="diagnostics_close">Fechar</string>
</resources>
''';

def one(text: str, old: str, new: str, name: str) -> str:
    count = text.count(old)
    if count == 1:
        return text.replace(old, new, 1)
    if count == 0 and new in text:
        return text
    raise ValueError(f"{name}: expected exactly 1 original anchor, got {count}")

def patch_diagnostics(s: str) -> str:
    s = one(s, '    private TextView status;\n',
            '    private TextView status;\n'
            '    private String tx(int id) { return TbxLanguage.text(this, id); }\n'
            '    private String txf(int id, Object... args) { return TbxLanguage.format(this, id, args); }\n',
            "helper methods")
    s = one(s, 'title.setText(R.string.diagnostics_title);',
            'title.setText(tx(R.string.diagnostics_title));', "title")
    s = one(s, 'status.setText(intro);', 'status.setText(tx(intro));', "intro initial")
    # There are two instances of status.setText(intro), after reversion to intro;
    # patch the second one if still present.
    s = one(s, 'status.setText(intro);', 'status.setText(tx(intro));', "intro refresh")
    s = one(s, 'button.setText(text);', 'button.setText(tx(text));', "buttons")
    for key in ("diagnostics_working", "diagnostics_exported",
                "diagnostics_no_report", "diagnostics_view_log"):
        # view_log is also the title of the dialog, not just a button
        anchor = "status.setText(R.string."+key+");" if key != "diagnostics_view_log" else "title.setText(R.string.diagnostics_view_log);"
        new = anchor.replace("R.string.", "tx(R.string.").replace(");", "));")
        s = one(s, anchor, new, key)
    old = "status.setText(getString(R.string.diagnostics_failed, String.valueOf(error.getMessage())));"
    new = "status.setText(txf(R.string.diagnostics_failed, String.valueOf(error.getMessage())));"
    if s.count(old) == 2:
        s = s.replace(old, new)
    elif s.count(old) == 0 and s.count(new) == 2:
        pass
    else:
        raise ValueError("diagnostic error formatter changed")
    s = one(s, 'getString(R.string.diagnostics_title), uri',
            'tx(R.string.diagnostics_title), uri', "share title")
    return s

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("starling_source", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = args.starling_source.resolve()
    if not (root / "Cargo.toml").is_file():
        ap.error("Not a Starling source checkout")

    src = root / "packaging/android/java/io/github/juanluci/starling/DiagnosticsActivity.java"
    target = patch_diagnostics(src.read_text(encoding="utf-8"))
    java = root / "packaging/android/java/io/github/juanluci/starling/TbxLanguage.java"
    resource = root / "packaging/android/res/values-pt-rBR/diagnostics.xml"
    for f, data in ((java, HELPER), (resource, PT)):
        if f.exists() and f.read_text(encoding="utf-8") != data:
            raise ValueError(f"Refusing to overwrite a different upstream file: {f}")
    if args.check:
        print("PASS: Android recovery i18n anchors and pt-BR strings checked; no APK.")
        return
    src.write_text(target, encoding="utf-8")
    for f, data in ((java, HELPER), (resource, PT)):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(data, encoding="utf-8")
    print("Android recovery UI now uses language in game options.txt (pt_br/en_us).")
    print("Raw technical logs and driver error messages remain unchanged; no APK built.")


if __name__ == "__main__":
    main()
