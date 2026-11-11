# Replay and evidence boundaries

Run from repository root. Requires existing Python3, Node and macOS `sips` for original JPEG decoding. No package installation or paid service is part of replay. Native frames, full campaign, exact parameter freezes, independent input/oracle packets and checker code are retained. The raw JPEG is the capture; decoded/cropped PNG is an analysis copy with JPEG ancestry.

The browser corpus was already executed and independently checked. These commands regenerate an analysis on saved inputs, not a new Garmin/human experiment. Replaying a green check is optional for a new reviewer; the original receipts remain authoritative for this run.

```sh
mkdir -p .cache/spacefox-marker-replay
python3 openspec/changes/make-launch-site-obvious/evidence/reviewer/export_assets.py \
  openspec/changes/make-launch-site-obvious/evidence/campaign.json.gz \
  .cache/spacefox-marker-replay \
  --stage confirm \
  --frozen-candidates openspec/changes/make-launch-site-obvious/evidence/final-freeze.json \
  --oracle openspec/changes/make-launch-site-obvious/evidence/confirm24/oracle.json \
  --native-oracle openspec/changes/make-launch-site-obvious/evidence/confirm24/oracle.json \
  --native-dir openspec/changes/make-launch-site-obvious/evidence/native/confirm

python3 openspec/changes/make-launch-site-obvious/evidence/reviewer/audit_marker_raster.py \
  .cache/spacefox-marker-replay/native-manifest.json \
  .cache/spacefox-marker-replay/native-oracle.json \
  .cache/spacefox-marker-replay/native-result.json \
  --proof-layer native \
  --frozen-candidates openspec/changes/make-launch-site-obvious/evidence/final-freeze.json

python3 openspec/changes/make-launch-site-obvious/evidence/reviewer/audit_visible_masks.py \
  .cache/spacefox-marker-replay/geometry-manifest.json \
  .cache/spacefox-marker-replay/visible-mask-result.json

node openspec/changes/make-launch-site-obvious/evidence/reviewer/audit_semantics.js \
  openspec/changes/make-launch-site-obvious/evidence/campaign.json.gz \
  confirm \
  openspec/changes/make-launch-site-obvious/evidence/confirm24/inputs.json \
  openspec/changes/make-launch-site-obvious/evidence/final-freeze.json \
  .cache/spacefox-marker-replay/semantics-result.json
```

Portable image packets have relative paths and separately retained original truth/lock/score receipts. Their `scores-*-portable.json` were rechecked only because artifact locations changed; responses, image/mask bytes, source coordinates, parameters and thresholds did not change. Do not count this path validation as another reviewer or another success.

The primary final packet has60unique images and120responses in two independent contexts. The two active sceneIDs happen to be one coordinate in RU/EN. Primary results are60correct positive location/meaning responses,53confidentnegative none,7negativeuncertainties and0inventedpoints. Negative uncertainties are not successful absence recognitions. The specific positive/negative rule existed before G1; see `negative-uncertainty-adjudication.md`.

The separate `geography-supplement` is post-primary coverage: two additional coordinates selected by geographic distance before image inspection, unchanged five/source,35images/one fresh context. It is not another fresh confirmation bank or a new generation. Its30positive answers are correct, four negative none, one negative uncertain; no invented point. The builder and its protocol are stored beside the packet.

For engineering observations, the prototype runs native390 DOM validation and actual390/222/195 CSS captures. A 222/195 native CSS capture is not a resized390 image. All652valid raw JPEG boards and2844watchcrop observations are counted in `capture-counts.json`; shared boards and repeated trials are dependent. Earlier72scaled boards/420crops are explicitly rejected.

The local unit owner has12exact test identities, observed green during this task. Directly invalidated geometry cases were rerun after AA guard changes; the changed qualification pair was exercised with a real retained healthy record and an invalid anchor. Other valid greens were retained per user instructions. The executable DAG/discovery structure validates. Full pinned `ready` would rerun the entire module and is not claimed here: the research acceptance uses retained named-test observations plus the source/native/image receipts, not a fabricated runner-backed readiness record. No native Garmin build, AOD/battery qualification or human recognition rate is claimed.
