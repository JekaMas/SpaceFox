# Localization artifact schema — safe interface

Image-only reviewers receive only neutral images and the prompt in protocol-review.md. Do not give them this truth file, marker masks, source scenes, old ranks/reviews or capture counterparts. Raw answer text and structured self-reports are retained unchanged. Each response context is scored separately.

```ts
interface Response { imageId:string; status:'located'|'none'|'unable';
  x:number|null; y:number|null; // actual image pixels, not percent or390-normalized
  classification:'launch-site'|'decorative'|'other'|'uncertain'|'none';
  confidence:'low'|'medium'|'high'; evidence:string; }
interface Answers { answers:Response[] }
interface Truth { profile:string;trials:Array<{
  candidate:string;scene:string; // private truth identifiers; never shown to reviewer
  imageId:string; image:{file:string;sha256:string}; size:390|222|195;
  expectedVisible:boolean;
  kind:'active'|'genuine-null'|'map-present-marker-hidden';
  // populated only for positive trials; mask from audited actual clipping/paint,
  // not an unclipped recipe. Kept private until all answers are locked.
  visibleGlyphMask?:{file:string;sha256:string;origin:[number,number]};
  anchor390?:[number,number];
}> }
interface ResponseLock { answersSha256:string;truthSha256:string;lockedAtUtc:string }
```

Scoring accepts the actual visible glyph silhouette including enclosed holes, expanded by6native390 pixels, or the true-anchor disk of the same radius. This prevents a false miss when the reviewer points correctly into a hollow ring/pin interior. Positive `unable`, wrong location or wrong semantic identity is a material failure. Any asserted point on either negative kind is a false positive. Negative `unable` is retained as uncertainty and is not relabeled a confident `none`; it does not invent a point.

No source-map coordinate is disclosed to the image-only reviewer. The private truth manifest and answer lock bind image bytes, masks and complete response IDs. Local timestamps/hashes provide integrity bookkeeping, not an external chronology attestation or proof of psychological blinding. Report crops versus unique captures, reviewer contexts and trial dependence explicitly.

The scorer also requires an external frozen candidate-ID file. Final-profile validation checks exactly five candidates and60 images, with two distinct active scenes, one genuine null and one hidden-marker catch at each of the three sizes per candidate. Missing a whole candidate cannot silently shrink the denominator.
