"""TBX JAR-to-Rust port workspace tests. Never executes Java or builds an APK."""
import importlib.util
import json
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

MODULE = Path(__file__).with_name("tbx_mod_rust_assistant.py")
spec = importlib.util.spec_from_file_location("tbx_mod_rust_assistant", MODULE)
import sys
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class TestModAssistant(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def archive(self, name="test.jar", entries=None):
        out = self.root / name
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path, content in (entries or {}).items():
                zf.writestr(path, content)
        return out

    def test_fabric_metadata_and_rust_scaffold_without_claiming_conversion(self):
        jar = self.archive(entries={
            "fabric.mod.json": json.dumps({"id": "example_mod", "name": "Example Mod", "version": "1.2.3"}),
            "example/Entry.class": b"\xca\xfe\xba\xbe\x00\x00",
            "assets/example_mod/textures/block.png": b"\x89PNG\r\n",
            "data/example_mod/recipes/sample.json": b"{}",
        })
        info = module.scan(jar)
        self.assertEqual((info.mod_id, info.framework), ("example_mod", "Fabric"))
        self.assertEqual(len(info.classes), 1)
        self.assertEqual(len(info.resources), 2)
        output = self.root / "port_result"
        module.prepare(info, output, True)
        data = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
        self.assertFalse(data["playable"])
        self.assertFalse(data["compiled"])
        self.assertTrue(data["needs_manual_rust_port"])
        self.assertTrue((output / "resources/assets/example_mod/textures/block.png").exists())
        self.assertTrue((output / "resources/data/example_mod/recipes/sample.json").exists())
        self.assertIn("ORIGINAL_MOD_ID", (output / "src/lib.rs").read_text())
        self.assertFalse(any(output.rglob("*.apk")))
        with self.assertRaises(ValueError):
            module.prepare(info, output, True)

    def test_rejects_traversal_and_absolute_path(self):
        for dangerous in ("../secret.txt", "/root/escape", "assets\\evil.png"):
            jar = self.archive("bad.jar", {dangerous: b"fake"})
            with self.assertRaises(ValueError, msg=dangerous):
                module.scan(jar)

    def test_rejects_symlinks(self):
        output = self.root / "link.jar"
        with zipfile.ZipFile(output, "w") as zf:
            z = zipfile.ZipInfo("assets/sample/link")
            z.create_system = 3
            z.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(z, "../target")
        with self.assertRaises(ValueError):
            module.scan(output)

    def test_rejects_duplicate_paths(self):
        output = self.root / "dupe.jar"
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(output, "w") as zf:
                zf.writestr("foo.class", b"a")
                zf.writestr("foo.class", b"b")
        with self.assertRaises(ValueError):
            module.scan(output)

    def test_empty_jar_is_not_playable(self):
        jar = self.archive("empty.jar", {"META-INF/MANIFEST.MF": "Manifest-Version: 1.0"})
        info = module.scan(jar)
        self.assertEqual(info.framework, "Unknown")
        self.assertFalse(module.report(info, False)["playable"])
        self.assertFalse(module.report(info, False)["needs_manual_rust_port"])

    def test_preflight_shows_required_dependencies_without_running_a_jar(self):
        import tbx_mod_install_preflight as installer
        jar = self.archive("dependencies.jar", {
            "fabric.mod.json": json.dumps({
                "id": "test_mod",
                "name": "Test Mod",
                "version": "1.0",
                "depends": {"fabricloader": ">=0.16", "fabric-api": "*"}
            }),
            "example/Mod.class": b"\\xca\\xfe\\xba\\xbe",
        })
        scan = installer.preflight(jar, True)
        self.assertEqual(scan["loader"], "Fabric")
        self.assertFalse(scan["automatically_compatible_with_tbx"])
        self.assertFalse(scan["native_starling_compile_supported"])
        self.assertEqual({d["mod"] for d in scan["declared_dependencies"]},
                         {"fabricloader", "fabric-api"})


if __name__ == "__main__":
    unittest.main()
