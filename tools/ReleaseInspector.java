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
        if (args.length < 3) throw new IllegalArgumentException("IQ, public key and PRGs required");
        RSAPublicKey key = (RSAPublicKey) KeyFactory.getInstance("RSA").generatePublic(
            new X509EncodedKeySpec(Files.readAllBytes(Paths.get(args[1]))));
        if (key.getModulus().bitLength() != 4096 || !VerifyingUtils.verifyIqFile(new File(args[0]), key))
            throw new SecurityException("IQ signature or public identity mismatch");
        for (int i = 2; i < args.length; i++) {
            DeveloperSignature signature = VerifyingUtils.getVerifiedDeveloperSignature(new File(args[i]));
            if (!new BigInteger(1, signature.getModulusBytes()).equals(key.getModulus()) ||
                !BigInteger.valueOf(signature.getExponentAsInt()).equals(key.getPublicExponent()))
                throw new SecurityException("PRG signature or public identity mismatch: " + args[i]);
        }
        System.out.println("{\"iq_signature_verified\":true,\"prg_signature_verified\":true,"
            + "\"prg_public_key_matches\":true,\"rsa_bits\":4096,\"verified_programs\":" + (args.length - 2) + "}");
    }
}
