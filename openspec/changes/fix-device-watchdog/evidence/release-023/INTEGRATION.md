# B2 and live-data integration

The public main advanced from c410eb4e to 586212b9 during peer review. The
integration preserves B2's source-qualified unmatched world map and uncertain
point, including pending LOW and the temporary active presenter. It retains the
user-approved display-only `~` announced-NET reference, so minute precision has
one prefix and scheduling/reminders still use source precision. Optional world
map drawing and helpers are paged with `:extendedCode` to preserve SFR memory.
The original B2 and previous peer receipts remain unchanged.

The directly affected SDK FR165M selectors for unmatched LOW/pending drawing,
accepted facts, captured hour precision, bounded decode, heap reserve and
rollover passed; their individual logs are under `receipts/`. The matched real
capture gen56→gen57 was seeded by production storage/transfer primitives in an
isolated test UUID. A direct marker flip and onBackgroundData injection occurred
while SFR was active; the observed sequence canceled the old decoder, accepted
the new feed and completed its normal renderer (`pair-app-resume.log`,
`pair-final.png`, 111,384 bytes sampled, not a peak). One controlled simulator
restart retained seeded state after an SDK handshake deadlock; the unacknowledged
launcher and old event-cleanup attempts are preserved separately. This does not
prove phone HTTP delivery, hardware LOW transition or physical 15-minute success.

The earlier physical 0.1.20 owner report remains a failure witness: its missing
update cause is not established. No current on-watch pass or Store submission is
claimed by these software observations.

Independent merge peer review found and repaired a cold-LOW regression: the default backdrop had been used as a qualified-point flag. The backdrop is now independent of `qualifiedPin`, so no context means no fabricated point/badge. The one affected LOW selector passed with actual renderer/SceneAod call tracing, while earlier groups/replacement/RU/font proof remains retained. Final version/native ID is 0.1.23/600d5e50; the applicability positive and native-repin negative pass. See `PEER.md`; physical status is unchanged and author packaging/publication is next.
