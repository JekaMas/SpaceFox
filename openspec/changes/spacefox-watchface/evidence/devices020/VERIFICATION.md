# Iteration 020 verification graph

Status: scoped author and independent software verification GREEN; exact receipts, corrections and limits are recorded in [APPLY.md](APPLY.md) and [PEER.md](PEER.md). Root judgment and physical/phone/power/Store acceptance remain separate.

- D1 inventory → admission: enumerate every installed device directory, retain
  names/parts/capabilities and explicit reasons; reject absent watchface,
  API below 5.1, each resource below its floor, unqualified display or font,
  and altered/missing pinned profile inputs. Positive: each admitted device
  has watchface, supported API and all limits, with matching pins.
- D2 cohort coherence depends on D1: manifest product order equals lock and
  release selection. Negative: added, removed or changed product/pin is refused.
- D3 layout depends on D1: centered uniform 390 canvas preserves circular map,
  point and rocket alignment on round and rectangular views; negative: independent
  x/y scaling or off-screen viewport fails. Both LOW and NOT_LOW retain required
  content and four active fields.
- D4 fonts depend on D1: supported Latin/Cyrillic vector face is chosen on each
  admitted family; missing scalable font or glyph/fit regression is refused.
  Confirm EN/RU on representative families and preserve honest five-language
  qualification boundaries.
- D5 compile depends on D1–D4: actual SDK compiler result for every newly
  declared profile with exact profile/runtime hashes and production-equivalent
  code and flags; record any failures without retry erasure.
- D6 runtime depends on D3–D5: owned simulator observations of representative
  new dimensions, font and shape families in EN/RU and both modes, including
  field, map, point and text readability; no claim of physical or Store proof.
- D7 documentation depends on D1–D6: list all profile decisions, part aliases,
  source versus released scope and staged future admission criteria.

Execution order is D1–D4 → D5/D6 → D7; tests and documented negative cases
must exercise behavior or a real boundary, rather than repeat an implementation.
