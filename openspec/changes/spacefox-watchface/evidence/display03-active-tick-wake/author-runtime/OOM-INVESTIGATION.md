# Ordinary watchface out-of-memory observation — OPEN

The unmodified submitted signed 0.1.10 program admitted the actual hosted
Vulcan/Cape launch into its own fresh simulator storage. Without clearing
that storage, a production-identity/key diagnostic watchface observer compiled
from the candidate 0.1.12 native source (ID `40597c44`, FR165 Music, ordinary
watchface heap 126784 bytes) reopened the launch and rendered its marker and
countdown before optional reload. The observer wraps actual framework callbacks
and selects English or Russian through an isolated application property; its
entry point and logging are diagnostic, not an exported release artifact.

`candidate.log` records warm English startup and wake; `russian.log` records the
Russian restart, LOW, a manually delivered SDK Temporal Event, wake, and an
uncaught `Out Of Memory Error` after the reload and several active updates. No
stack symbol was reported. This is a failed ordinary-app integration, regardless
of the 10/10 separate SDK unit table. The failure point in a particular owner is
not yet established. The simulator runtime and ini were restored byte-for-byte;
original temporal registration remains unverified. The four PNGs are SDK screen
captures before the failure, not physical images.

Competing hypotheses: (1) the extra derived-outline bitmap, retained scanline or
its construction increases the live decoder peak; (2) the additional local
outline/resource references or other wake/restore retained state consume the
ordinary app heap before decoding; (3) observer logging/entry overhead or an
existing scene-delivery failure, unrelated to the new outline, explains the
failure. The current trace cannot distinguish them. The next experiment will
measure used memory at actual lifecycle and decoder boundaries and compare a
source-identical observer against a diagnostic-only variant that suppresses
outline work, retaining same real hosted input and app heap. Neither variant is
release evidence or grounds to claim a physical cause.
