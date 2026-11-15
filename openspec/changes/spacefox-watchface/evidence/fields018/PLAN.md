# Model-aware custom fields and regular release 0.1.18

Status: NOT DONE. Base: public main `28017c7bb2e9ca7c729f62c5a05cc7d3920ecf05`.
This is one coherent iteration under existing tasks 2.3, 5.1, 5.4 and 7.2/7.3;
the existing tasks.md remains the sole numbered task list.

## Outcome

Expand each of the four independently configurable ACTIVE fields from the
current six choices to all readings/complications exposed to a watch face by
the actual supported device's public Garmin APIs. Use runtime capability and
Complications enumeration, not a per-model hardcoded allowlist. Include system
and accessible user complications, numeric and string values, and relevant
nondeprecated ActivityMonitor daily values not exposed as complications.
Unavailable proprietary Garmin information is not invented. An available
field with a temporarily null reading remains selectable and displays the
unavailable marker; it is distinct from an unsupported capability.

Retain the existing four positions, colors, English defaults, persisted six
selection IDs, countdown/map/launch behavior and two display layouts. LOW
continues to omit the four fields. Read/subscribe only to selected unique
sources, use one complication callback owner, stop work/subscriptions in LOW
or when hidden, and avoid extra network requests or raw sensor activation.

The same registry/capability rules must work when a qualified new model is
added to the normal supported-device cohort. New SDK/firmware complication
types should use their reported label/unit/value through the generic path,
without another list of device-name conditions. Keep settings usable on the
watch and in the existing phone settings surface; document real platform
constraints accurately and implement a practical model-aware selection path.

## Acceptance and evidence

Keep source references to official Complications/Iterator/Id/Storage and
ActivityMonitor APIs. Verify real field discovery, per-slot independent and
duplicate assignments, stable persistence/restart and existing selections,
null/unavailable values, unit-aware numeric/time/string formatting, current
and later-profile capability variation, selection lifecycle and resource
bounds. Verify actual native EN/RU settings-to-render at 390 and 454 where
affected, with readable bounded field values/icons and unchanged layout.
Compile all current supported profiles for release; future-profile support
must follow the generic capability path rather than pretend untested models
are already qualified. No unsupported API or permission claim.

Use the existing real UI/source corpus and meaningful technical controls.
Record failing counterexamples, actual observations and exact source/input
bindings. Reuse noninvalidated greens. No typography research, general parser
rewrite, broad historical suite, synthetic Unicode campaign, paid API or
provider refresh is part of this iteration.

One fresh Terra 6.1 xhigh worker owns full APPLY/self-VERIFY/fix to GREEN; then
one fresh Terra 6.1 high peer owns independent VERIFY/fix to GREEN. Root judges
the result, performs one final main conflict/integration check, signs and tags
the higher version, publishes a regular GitHub release and updates the original
Garmin listing. Existing publication/agreement authority is already granted.
Physical installation and behavior remain unobserved until actual evidence.

## Prior unmerged-work audit

The read-only audit examined 248 local heads plus current origin refs: 45 are
ancestors of public main and 203 are not. Of 53 recent nonancestor heads, 50
are ancestors of accepted private authoring `ea64c08b`; its whole watchface,
tools/spacefox, cloud-feed, catalog, schemas, assets and locales scopes match
accepted public integration `4d813e1f`. The three recent exceptions were
reconciled to public counterparts (UI PR13, cleanup PR4, preflight PR6).
Image pipeline PR28, reminders PR29 and predecessor/publication PR30 are
already transferred; current image owners are byte-identical to their peer.
Eight likely current worktrees were clean. No ready absent production delta
was identified. Thirty-four older historical/other refs were not individually
requalified; these are not silently classified as green or merged. Never merge
the private authoring main or retired experiments into the public tree merely
because their ancestry differs.
