package dev.tbx.hybrid;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public final class TbxArchiveInspectorTest {
    static File sample(String suffix, String... names) throws Exception {
        File f=File.createTempFile("tbx-test-",suffix); f.deleteOnExit();
        try (ZipOutputStream out=new ZipOutputStream(new FileOutputStream(f))) {
            for (String name:names) {
                out.putNextEntry(new ZipEntry(name));
                out.write(123); out.closeEntry();
            }
        }
        return f;
    }
    static void check(TbxArchiveInspector.Kind expected, File f) throws Exception {
        TbxArchiveInspector.Kind got=TbxArchiveInspector.inspect(f).kind;
        if (got!=expected) throw new AssertionError("wanted "+expected+" got "+got);
    }
    public static void main(String[] args) throws Exception {
        check(TbxArchiveInspector.Kind.JAVA_MOD,sample(".jar","fabric.mod.json"));
        check(TbxArchiveInspector.Kind.JAVA_MOD,sample(".jar","META-INF/neoforge.mods.toml"));
        check(TbxArchiveInspector.Kind.RESOURCE_PACK,sample(".zip","pack.mcmeta"));
        check(TbxArchiveInspector.Kind.HORIZON_SHADER,sample(".hshader","horizon-shaders.toml"));
        check(TbxArchiveInspector.Kind.CLASSIC_SHADER,sample(".zip","shaders/program/test.fsh"));
        check(TbxArchiveInspector.Kind.UNKNOWN,sample(".zip","readme.txt"));
        try {
            TbxArchiveInspector.inspect(sample(".zip","../escape.txt"));
            throw new AssertionError("unsafe path accepted");
        } catch (IOException expected) { }
        System.out.println("PASS: TBX Java archive classification and path safety.");
    }
}
