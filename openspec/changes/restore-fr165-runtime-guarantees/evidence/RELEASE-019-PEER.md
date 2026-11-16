# Independent 0.1.19 release-delta and artifact review

**Verdict: software and artifact GREEN for the authorized GitHub test
prerelease, subject to root judgment and publication.** This does not establish
physical FR165 P1–P3, phone/update migration, or a Garmin Store submission or
approval. B2 and B3 remain open. The owner reported that physical 0.1.18 was
installed and then showed missing point/time and an IQ error; its cause remains
unknown. The owner explicitly authorized test distribution before the physical
gate was satisfied.

## Source, admission and original export

Compiled source is `4f78ef39724c5760fa851da33419973a84b6fb36` (version 0.1.19,
native ID `2dc0a9bc`). The author handoff `3fdc5e6551bb93763d4de36cbad3d5ad127e08f0`
adds only artifact evidence and a checklist update. Relative to the independently
reviewed B1 commit `0173de8bdc28fc42c55851207c084665a85885e1`, the only native
source change is the generated version identifier, with the corresponding
manifest version change. The final peer commit adds documentation and review
evidence; its later tag or merge revision is not the compiled source.

Inspected the current B1 admission owner, its input and evidence inventories,
locale-policy baseline, exact 16-file B1/version delta, version generator,
source export integration and focused negative tests. The update guard checks
same production UUID and SPKI, a strictly higher version and an actual retained
predecessor IQ matching its original receipt. The original 0.1.18 receipt and
IQ independently matched SHA-256
`bfe206bac41a83913404c738d4796e52e9d960863ac4674ea12968f082942c77` and
`389d7e05b061f8621fb0792291cb1acb5e7f20f71ad6fa04dfe00f3e46cf5a36`.
The author-reported four admission tests retain their original results; this
review did not rerun an unchanged test set.

The original candidate build timed out at the IQ export after 240 seconds;
`FAILED.json`, the outer timeout log, 42 successful compile logs and rejected
standalone files remain in the author's external build directory. Independently
compared all 42 rejected standalone files byte-for-byte with the continuation
assets. The continuation script rechecked the source snapshot, generated
manifest/jungle, toolchain, original predecessor and public identity before its
IQ-only export with a 900-second bound. The success receipt records that
continuation rather than claiming an uninterrupted 43-command run.

## Actual asset checks

The author's original 56-file asset directory is retained unchanged. Its
`SHA256SUMS.txt` SHA-256 is
`51c85e8747a7caca85ef82e035d0d9de57b133d4108e72161ebd90add5de0527`.
An independent pass verified all 55 listed assets against that manifest and
matched the 42 PRGs and IQ to the original release receipt. All 6,528 source
archive inputs matched both receipt SHA-256 values and Git blob identities at
compiled revision `4f78ef39`; the two generated inputs matched the receipt.
The source ZIP had no duplicate entries, key-like filenames or private-key PEM
headers. These checks do not claim detection of every possible secret encoding.
The original install ZIP's contents and internal checksums matched its assets.

Using the supplied public SPKI and pinned SDK `ReleaseInspector`, an independent
cryptographic check passed the IQ, all 42 standalone PRGs and both extracted
FR165/FR165 Music IQ programs: 44 verified PRGs, RSA4096. The extracted FR165
and FR165 Music bytes exactly match the corresponding standalone PRGs. The
actual IQ manifest matched the production identity, version, languages and
permissions; all 49 part/profile mappings matched the receipt. The author's
original receipt separately records the larger 91-program inspection, retained
at its original boundary. The first peer verification script assumed every
profile declared a minimum firmware and raised `KeyError`; it was corrected to
allow the same absent-field case as the release inspector before the successful
verification. This was a peer harness error, not a package failure.

## Documentation repair and corrected handoff

The staged installation guide linked to a testing file and publication record
that were absent from the install ZIP, and its final unqualified physical
statement was ambiguous beside the owner's observed 0.1.18 installation. The
peer changed the guide to link the included `TESTING-0.1.19.md` and the pinned
public 0.1.18 record, and explicitly scoped the unverified physical statement to
0.1.19. The test instructions are now also present in the repository. These
are post-compile documentation changes; the original source ZIP remains the
exact 4f78 compiler-input snapshot.

The corrected external 56-file asset directory is
`/Users/jekamas/.codex/tmp/spacefox-b1-release-019-peer-final-assets-20261116/`.
Its install ZIP contains the same eight intended files; all relative Markdown
links in its user-facing guides resolve within the ZIP, each member matches the
corresponding asset, and internal checksums and ZIP CRC pass. Five files differ
from the retained original directory: installation guide, install ZIP,
verification, provenance and checksum manifest. The other 51 files, including
all signed programs, receipt and source ZIP, are byte-identical to the original.
The first peer correction linked the publication record at the earlier 0.1.18
compiled revision, where that later record does not exist. That intermediate
asset directory was retained; the final guide points to the verified record at
public base `29f3cfd`, and the final manifest was regenerated after this fix.

| Corrected asset | SHA-256 |
| --- | --- |
| `SHA256SUMS.txt` | `a19d076d8574775c332731165b908443bd49f579a854da7a2f66c4495911eaa7` |
| `SpaceFox-0.1.19-FR165-install.zip` | `5e4767e79ae3713a43c4864c67075209f8eb8435b25212fa812c61164d85b4e0` |
| `INSTALLATION.md` | `911beb5881a0d2125a0f4c58bee517613f467c7ed7ce1ffa3586c1bec692a8c7` |
| Unchanged `SpaceFox.iq` | `2c4ae33b3745878b84eb0917c58a614b195ec2b7f61bbc499fe10f00bf2849e1` |
| Unchanged FR165 and FR165 Music PRGs | `7bd7b33bc9d6a7f8e4d1e446f30c0777e1ba5e39b14ce4b94431a4652ee7c9f0` |
| Unchanged source-input ZIP | `3684a26ae4ba19995b66b2b0ad53efadf04dd9d5dbdad2198ba0918d6bf87097` |
| Unchanged original `release.json` | `e9afd8a607ba6ef49e96eb0c60f19095ccbfdb2fe129207dbad7d2bba9135211` |

The GitHub current-motion CI success referenced in the author provenance is
for compiled source `4f78ef39`; it was not independently rerun here. The B1
950-second SDK observation remains bound to `d1263b37`, not this signed
candidate. Physical cold start, reopen, ACTIVE/LOW/OFF and at least 15 minutes
on the exact FR165 candidate remain required observations. The current record
is an independent pre-publication review, not evidence that a tag, release,
Store action, installation or physical acceptance occurred.
