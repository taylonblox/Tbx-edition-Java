package dev.tbx.hybrid;

import java.io.File;
import java.io.IOException;
import java.util.Enumeration;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/** Classifies an archive's data; never loads or executes JAR code. */
public final class TbxArchiveInspector {
    private TbxArchiveInspector() {}
    public enum Kind { JAVA_MOD, RESOURCE_PACK, HORIZON_SHADER, CLASSIC_SHADER, UNKNOWN }
    public static final class Verdict {
        public final Kind kind;
        public final String loader;
        public final String detail;
        public final int entries;
        Verdict(Kind kind, String loader, String detail, int entries) {
            this.kind = kind; this.loader = loader; this.detail = detail; this.entries = entries;
        }
        public String toString() { return kind + " / " + loader + ": " + detail; }
    }
    public static Verdict inspect(File file) throws IOException {
        if (file == null || !file.isFile()) throw new IOException("Archive not found");
        boolean fabric=false, quilt=false, forge=false, neo=false, resource=false, nativeShader=false, classicShader=false;
        int entries=0;
        long total=0;
        try (ZipFile zip = new ZipFile(file)) {
            Enumeration<? extends ZipEntry> all=zip.entries();
            while (all.hasMoreElements()) {
                ZipEntry item=all.nextElement();
                String name=item.getName().replace('\\','/');
                if (name.startsWith("/") || name.equals("..") || name.startsWith("../")
                        || name.contains("/../") || name.matches("^[A-Za-z]:.*"))
                    throw new IOException("Unsafe archive path");
                if (++entries > 20000) throw new IOException("Archive has too many entries");
                long bytes=item.getSize();
                if (bytes > 0) {
                    if (bytes > 512L*1024*1024-total) throw new IOException("Archive expanded size too large");
                    total+=bytes;
                }
                String lower=name.toLowerCase(Locale.ROOT);
                if (lower.equals("fabric.mod.json")) fabric=true;
                if (lower.equals("quilt.mod.json")) quilt=true;
                if (lower.equals("meta-inf/mods.toml")) forge=true;
                if (lower.equals("meta-inf/neoforge.mods.toml")) neo=true;
                if (lower.equals("pack.mcmeta")) resource=true;
                if (lower.equals("horizon-shaders.toml")) nativeShader=true;
                if (lower.startsWith("shaders/") && !item.isDirectory()) classicShader=true;
            }
        }
        if (fabric || quilt || neo || forge) {
            String loader=fabric?"Fabric":quilt?"Quilt":neo?"NeoForge":"Forge";
            return new Verdict(Kind.JAVA_MOD, loader,
                "Recognized Java mod. Requires a compatible JVM and Minecraft Java engine.", entries);
        }
        if (file.getName().toLowerCase(Locale.ROOT).endsWith(".jar"))
            return new Verdict(Kind.JAVA_MOD,"unknown","Unrecognized JAR metadata; cannot run in native Rust.",entries);
        if (nativeShader) return new Verdict(Kind.HORIZON_SHADER,"Horizon","Requires game shader validation.",entries);
        if (classicShader) return new Verdict(Kind.CLASSIC_SHADER,"Iris/OptiFine","Renderer compatibility not guaranteed.",entries);
        if (resource) return new Verdict(Kind.RESOURCE_PACK,"Minecraft","Resource-pack structure found.",entries);
        return new Verdict(Kind.UNKNOWN,"unknown","Archive not recognized.",entries);
    }
}
