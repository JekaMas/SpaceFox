# Root judgment — hosted rollover delivery

The local hosted-delivery repair is DONE. Root accepts author `9ab7ec3b` and
independent review `849ad4d2`. The peer found no further source or test repair;
it independently authenticated all 279 fixture paths/bytes and reviewed the
two candidate paths, immutable pending recovery, exact journal/readback, bounds
and historical receipt fallback. Its report is an evidence/source review, not
a second behavioral run. Valid author greens were reused.

Root explicitly authorizes and discloses the specification correction from
256 complete-delivery paths to 512 = 2 × 256. The captured failure contains
274 reachable paths / 864,544 bytes from two individually valid snapshots;
there is no dead-file cleanup that preserves their required exact closures.
This corrects a self-imposed publisher design contradiction within the owner's
instruction to fix found defects and update the specification. It is not a
hidden limit increase. The individual 256-path limit, complete 1 MiB byte
limit, native 8 KiB feed limit, CAS, source-age/quota and exact HTTPS readback
remain. The new preflight refuses an impossible future union before persisting
pending; it does not discard or reconstruct the existing pending 49.

Root reviewed the production diff and independent report. The captured RED,
real 274-path regression, guard/preflight/binding cases and five affected
recovery checks are GREEN. Local recovered 49 and newly prepared 50 passed
simulated finality and exact readback; 50 has two upcoming entries, 166 paths
and 584,666 bytes with no provider call or source-age/quota change.

This is a host-only revision. The released native 0.1.17 / `2e6fc8c4`, source
`bc744093`, signed package, original receipt and tag remain immutable. Their
observed greens are not invalidated by the host guard and historical fallback.
No native or locale replay is required for publication of this host repair.

Live integration and two serialized workflow runs remain open: first deliver
the exact pending 49, then deliver the new upcoming metadata. Only actual live
readback after the second delivery closes hosted activation. Physical watch
delivery remains separately unobserved.
