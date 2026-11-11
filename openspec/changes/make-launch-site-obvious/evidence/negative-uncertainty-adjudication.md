# Independent adjudication — negative uncertainty

This note was written after the final reviewer answers were locked. It applies the already recorded pre-G1 rule; it does not introduce an exception, adjust a threshold or change the scorer.

**An `unable` answer on an intentionally negative image is recorded uncertainty, not a material false positive.** An `unable` answer when a visible marker is expected remains a material localization failure. An asserted point on either genuine-null or map-present/marker-hidden images remains a false positive.

The controlling specific definitions existed before generation1:

- Frozen reviewer `protocol-review.md:65` names “unable on a non-null scene” among material failures. Its meaning is a marker expected to be visible, not inability to find an intentionally hidden mark.
- The accepted pre-G1 addendum at `protocol-review.md:89` explicitly separates `none`/`unable` on negative images and defines a fabricated point as the negative-trial failure; positive inability, wrong position or wrong meaning is a material failure. It also explicitly places marker-hidden counterfactuals in the negative group despite a non-null source coordinate.
- Frozen `localization-schema.md:24` says negative `unable` remains uncertainty, is not relabeled confident `none` and does not invent a point.
- Frozen `score_localization.py:48` rejects positive inability; lines53–54 reject an asserted negative point and separately flag negative uncertainty. This implementation predates the observed final answers and is unchanged.

An unqualified design-prose statement such as “unable fails” must be read with those explicit positive/negative definitions. Clarifying that prose with a link to the original specific rule is an editorial consistency correction, not a post-result rule relaxation. Preserve this clarification's chronology rather than rewriting an old protocol to look prescient.

The reported seven negative uncertainties therefore do not by themselves require another repair or fresh bank. They remain seven nondecisions; they are not successful absence identifications. The correct reporting, **subject to checking locked positive coordinates and meaning**, is60 positive localization/meaning results across two reviewer contexts,53 confident negative `none` responses, seven negative uncertainties and zero invented negative points. Do not call that120/120 correct decisions,100% accuracy, confident absence recognition or human recognition evidence.

Six uncertainties reportedly concern the instrumented Ticket HIDE frames with the frozen `СТАРТ` context deliberately retained; these are artificial catch images, distinct from a failed visible-marker product state. The remaining genuine-null Atlas222 uncertainty is also retained. The two contexts inspect correlated images and are model/reviewer observations, not120 independent human participants.

The separate fresh source/native/mask tests and the independent positive coordinate/semantic scores must still pass before acceptance. This adjudication cannot rescue a misplaced visible marker, a positive inability or wrong meaning, or a false asserted point on a negative image.
