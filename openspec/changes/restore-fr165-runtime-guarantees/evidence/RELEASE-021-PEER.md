# Independent 0.1.21 artifact review

**Artifact verdict: GREEN for the authorized GitHub test prerelease**, subject
to root judgment, publication and public readback. This is not a physical FR165,
phone/update migration, Store approval, B2 or B3 acceptance. The owner reported
that physical non-Music FR165 installed 0.1.18 and then showed missing time/point
and an IQ error; its cause remains unknown. The owner authorized test
publication before physical P1–P3 acceptance. No Store action is implied.

## Frozen source, predecessor and export

The actual compiled main revision is
`98dc7a6e41f03e8904d1dd02ff941317d52eb5be`, version `0.1.21`, generated native
ID `e0ee18e0`. The original full receipt, IQ and 42 program assets remain
unchanged. A later documentation/review commit or tag is not the compiled
revision. The 0.1.20 locally retained original receipt SHA-256
`fbfe2da43812ebd01608ad177007743fb24a368b1a69d8a0823ed37e98956818` matches
the published package summary, and the matching published IQ SHA-256 is
`b5bd0cb73b290f37e49e5b5027a6304213dcb38bc5669cf220d6652b8c59738d`. The
full predecessor receipt was locally retained; it was not itself a public
release asset. The update preserves production UUID
`ec8b7c8a8ea54ee9ac91ee6e7a674d15` and RSA4096 public SPKI SHA-256
`84e95bea4f3052a7c93f297e25605dc374a02f946b8011c65eec950b284146cc`.

Inspected the actual IQ-first adapter and receipt: it runs one official full IQ
export with a 900-second limit, checks exact part membership and refuses
missing/duplicate/unsafe members or per-profile variant differences before
extracting programs. It calls the existing full SDK inspector. The receipt
explicitly records one compiler invocation and **zero independent standalone
compilations**. The sanitized SDK export log and warnings are included.

Independent actual-byte checks passed: the original 56-entry checksum manifest
matched every asset; all 6,657 source-input ZIP members matched both their
receipt SHA-256 and Git blob identity at the compiled revision, while the two
generated manifest/jungle members matched the receipt. The archive had no
key-like filenames or PEM private-key headers; these checks do not guarantee
detection of every possible secret encoding. Defaults in those frozen inputs
are English and `https://jekamas.github.io/SpaceFox`.

The actual IQ manifest matched version, UUID, entry, permissions and languages;
its 49 parts mapped completely to 42 declared profiles. Every member of every
profile was byte-identical to its corresponding extracted standalone PRG,
including FR165 and FR165 Music. An independent execution of the pinned SDK
verifier accepted the IQ and all 91 embedded/derived PRGs against the actual
production public SPKI. The original 0.1.20 receipt and IQ were rechecked,
without accessing production private key contents or performing a new export.

## Portable handoff corrections

The author's installation and testing guides instructed an owner to read
`e0ee18e0` in watch settings. `SettingsMenu` shows `NativeVersion.BUILD`, and
no settings owner reads `NativeVersion.ID`; therefore the corrected guides ask
for version 0.1.21 in settings and a PRG checksum comparison before copying.
The native ID remains traceable in package provenance, not claimed visible on
the watch.

The standalone third-party notices had 12 relative links to license or context
files missing from the download. The corrected notice points those links at
verified files in the exact frozen Git revision. The FR165 install ZIP and new
`SpaceFox-0.1.21-licenses.zip` include all 13 retained `licenses/` files and
the Unicode license with their original paths. ZIP member bytes match those
frozen Git files; both archives passed CRC checks, the install ZIP's internal
checksums match, and all relative Markdown links in the delivered documents
resolve. The original source-input archive also remains available. These
checks describe included notices, not a new legal opinion.

Provenance originally identified an externally retained IQ-first helper only by
hash. `BUILD-REPRODUCIBILITY.md` now honestly identifies that helper as not
distributed and describes the standard repository/SDK alternative and its
limitations, including that it is a different 42-standalone-plus-IQ build,
may time out, requires authorized production signing and the locally retained
0.1.20 full predecessor receipt, and does not promise bitwise reproduction.
No native source, signed program or compiler input was changed.

The original 57-file author asset directory and intermediate peer corrections
are retained. The final corrected external directory is
`/Users/jekamas/.codex/tmp/spacefox-b1-release-021-20261116/assets-peer-release/`:
59 files with 58 checksum entries. Seven original documentation, ZIP or manifest
files changed, two guidance/license assets were added, and the other 50 original
assets—including IQ, all PRGs, original `release.json` and source ZIP—were
verified byte-identical. No private-key header or local user path appeared in
the delivered text. Final changed-file checksums, ZIP CRC/member contents and
relative links were checked after the documentation batch stabilized.

| Final asset | SHA-256 |
| --- | --- |
| `SHA256SUMS.txt` | `3c75796bf8cc4df80a8f3d446e6941fbc39e029623cb0f514b913878dd76ecbb` |
| `SpaceFox-0.1.21-FR165-install.zip` | `f3b0973b3e072d7fe910cf51a54dca1f93226f3e78a383ceb2e39c0050597d58` |
| `SpaceFox-0.1.21-licenses.zip` | `79d3d9c119d6c3a8edd9a8781d87ea2e376b4412f15fa0bc74477190487c48ca` |
| Unchanged `SpaceFox.iq` | `c1e991af2372ce63dd35cba147ccb2075a6cd9b0e9a50844ad3533347653379b` |
| Unchanged FR165 and FR165 Music PRGs | `6ef6bc2dbebb5a1e3537c18a69db6a6f137b3e6ec66a2061b5355d3ce1ec5353` |
| Unchanged compiler-input ZIP | `761af3c30edf4f20deb5f23ad82f1d8c763dd2777b099d781b2353ddcc86d04d` |
| Unchanged original `release.json` | `d1d29b5d010f840acaf4fdb7734a2c3ea248ece3411ed914478abcdfe0bea2c1` |

The earlier B1 950-second run, author f29b60ca 55-second stock observation and
all other SDK receipts retain their original source/scenario identities; none
is a physical run of this binary. Source PR 38 and current-motion CI are
recorded separately from this artifact review. Exact 0.1.21 physical cold,
reopen, ACTIVE/LOW/OFF and at least 15 minutes ordinary FR165 use, plus phone
and update migration, remain unverified. This report does not claim publication
or Garmin review.
