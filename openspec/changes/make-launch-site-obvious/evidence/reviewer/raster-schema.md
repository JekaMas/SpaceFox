# Safe raster adapter interface (proposed; no holdout values)

The reviewer checker consumes a separate artifact manifest; it does not require changing the product scene schema. Keep raw old observation/oracle audits in addition. Paths resolve relative to the manifest folder, and SHA256 is required for every artifact. Diagnostic PNG alpha masks and decoded native JPEGs have different provenance.

```ts
interface Asset { file:string; sha256:string }
interface Capture extends Asset {
  // integer raw-image pixel crop: no guessed rescale/upsample
  faceRect:{x:number;y:number;w:390|222|195;h:390|222|195};
}
interface Component extends Asset {
  // a transparent RGBA reference from live computed marker paint;
  // preserves actual output-pixel phase, with >=2 transparent border pixels
  origin:[number,number]; // INTEGER top-left within the displayed face pixel grid
}
interface Trial {
  id:string; candidate:string; scene:string; size:390|222|195;
  sourcePoint:[number,number]|null;
  geometry:{
    anchor:[number,number]|null; // native390 logical units, true projected site anchor
    clips:Array<
      {role:'watch';kind:'circle';cx:195;cy:195;r:195}|
      {role:string;kind:'rect';x:number;y:number;w:number;h:number}>;
    // All foreground containers use actual computed paint channels, not a trusted painted:true.
    occluders:Array<{role:string;x:number;y:number;w:number;h:number;
      background:string;display:string;visibility:string;opacity:number}>;
    // Full required label/icon/badge/rocket boxes from the retained old observation.
    protected:Array<{role:string;x:number;y:number;w:number;h:number}>;
  };
  markerReferenceSvg:Asset|null; // serialized LIVE subtree with computed attrs/transforms/sizing
  masks:{glyph:Component;core:Component;halo:Component}|null;
  capture:{
    provenance:'native-jpeg'|'actual-viewport-png'|'diagnostic-export-only';
    on:Capture[]; hide:Capture[];
    // Native counterpart changes only site marker visibility. At least2 hide reps;
    // preferably2 on reps. Compare actual JSON descriptors, not supplied booleans.
    nonMarkerOn:Asset; nonMarkerHide:Asset;
  };
}
interface Manifest {schemaVersion:1;stage:string;trials:Trial[]}
```

`geometry` remains in390 logical units while the masks/crops are in actual output pixels. The unbounded reference alpha is clipped by the declared true watch/geo clips and attenuated by positive computed foreground paint. This is conservative source-bound coverage; native JPEG signal is a separate check, not alpha truth. A complex clip unsupported by this simple adapter must be exported as a lossless transmittance mask or rejected as unavailable rather than replaced with a guessed rectangle.

No-marker scenes require a null anchor/reference/masks and identical non-marker descriptors. The independent scene oracle, not the manifest's claim, determines whether a marker is expected. A separate complete scene/candidate/size coverage assertion is required at each frozen stage.

The checker decodes PNGs independently using stdlib code. JPEG decoding uses macOS sips to a temporary lossless analysis copy, retains raw input hashes and records JPEG ancestry; it does not relabel the result a lossless capture. Exact face crops and integer native dimensions are required. At least one real native image pair per claimed trial is needed to claim that trial passed native image support. A diagnostic-only trial cannot pass that native gate.

Noise support uses max-channel RGB deltas, HIDE/HIDE (plus ON/ON when supplied)99th-percentile noise, and a conservative threshold max(12/255,4×noise). The marker ROI is padded by at least16 **capture pixels** for JPEG DCT/chroma, including at the small sizes. Off-ROI or invalid/noisy comparisons are explicit instrumentation failures. Core eligibility alpha≥0.75, halo≥0.25; minimum eligible samples scale from12native pixels (with a floor2). These are declared engineering rules and sensitivity diagnostics, not perceptual physiology.

Use `--proof-layer geometry` for the complete source-bound mask corpus, or `--proof-layer native` for the explicitly selected actual-image subset. The latter also checks source geometry, plus actual ON/HIDE pairs. Pass a separate **frozen candidate-ID file** with `--frozen-candidates`; coverage is checked against that external set and the supplied independent oracle's complete scene set at all three sizes. Geometry-only does not count as native-image support. At screen, make a separate four-scene native oracle under the predeclared selection rule; all24 still have the geometry oracle. The full fresh confirm24 native set is not sampled down.
