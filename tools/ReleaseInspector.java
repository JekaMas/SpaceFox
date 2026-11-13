// Original SpaceFox adapter. Calls the pinned SDK verifier; contains no vendor source.
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.X509EncodedKeySpec;
import java.math.BigInteger;
import com.garmin.connectiq.common.signing.DeveloperSignature;
import com.garmin.connectiq.common.signing.VerifyingUtils;

class ReleaseInspector {
    public static void main(String[] args) throws Exception {
        RSAPublicKey key = (RSAPublicKey) KeyFactory.getInstance("RSA").generatePublic(
            new X509EncodedKeySpec(Files.readAllBytes(Paths.get(args[2]))));
        boolean iq = VerifyingUtils.verifyIqFile(new File(args[0]), key);
        DeveloperSignature signature = VerifyingUtils.getVerifiedDeveloperSignature(new File(args[1]));
        boolean matches = new BigInteger(1, signature.getModulusBytes()).equals(key.getModulus())
            && BigInteger.valueOf(signature.getExponentAsInt()).equals(key.getPublicExponent());
        if (!iq || !matches || key.getModulus().bitLength() != 4096) {
            throw new SecurityException("IQ/PRG signature or public identity mismatch");
        }
        System.out.println("{\"iq_signature_verified\":true,\"prg_signature_verified\":true,"
            + "\"prg_public_key_matches\":true,\"rsa_bits\":4096}");
    }
}
