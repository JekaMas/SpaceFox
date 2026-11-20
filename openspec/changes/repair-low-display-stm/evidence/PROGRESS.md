# Current

Candidate 0.2.19 / NativeID `e39b693d`: 54/54 permanent FR165/M runtime selectors passed on the final candidate (16 unchanged owner cases retained, 38 affected cases rerun), five current-primary selectors and 11 portable controls passed; the actual simulator OFF→LOW capture before that final redraw-only change retained its qualified point and countdown and measured 9,239 lit pixels. See `AUTHOR.md` for first RED, source ownership, observer limits and full logs. Clean source binding and independent peer remain open. The old change passes non-strict validation, while strict reports its unrelated unchanged long launch-schedule requirement warning.

## Initial finding

Base `7113edc9f168f3fc78645c1e059121d6dc36c3b9` (0.2.18). Code review identifies OFF represented as LOW, and `transitionMode` returns without LOW entry effects when OFF is followed by LOW. Separately `syncDisplayMode` combines raw OS mode with a potentially stale `sleeping` callback flag. Both hypotheses require production-view event witnesses; neither alone establishes the unobserved physical incident. Work in progress; no release or peer review yet.
