# LL2 contract fixtures

`page-normal.json` is an authored, anonymized normal-mode LL2 2.3 contract vector,
not a recording of a current worldwide schedule or a live API observation.
The shape and meaning were checked on 2026-11-12 against official primary sources:

- https://lldev.thespacedevs.com/2.3.0/launches/upcoming/?format=api documents
  normal/list/detailed modes, `include_suborbital`, `hide_recent_previous`, `net`
  ordering, count/next/results and max100 results; the normal example has nested
  configuration/operator/pad/country/mission and `last_updated`/NET/precision.
- https://lldev.thespacedevs.com/2.3.0/config/net_precisions/?format=api documents
  Second0/SEC, Minute1/MIN, Hour2/HR, Morning3/AM and Afternoon4/PM as local
  time;17 records paginate. This is development configuration, not a claim of
  a production enumeration. Unknown IDs stay coarse; no closed whitelist.
- https://github.com/TheSpaceDevs/Tutorials/blob/main/announcements/LL_230_changelog.md
  identifies InFlight6 and intermediate PayloadDeployed9, nonnull NET/window/status
  and image credit/license. No fixture imagery is imported or relicensed.
- https://github.com/TheSpaceDevs/Tutorials/blob/main/tutorials/getting_started_LL2/README.md
  gives the2.3 upcoming path and explicit pagination. `ll` has rate limits;
  `lldev` is development-only and must not be used as freshness proof.
- https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_TSD.md describes
  anonymous15/hour and cached distribution.

Docs were browsed; no production schedule requests were made. Tests mutate these
literal facts for rejection partitions. Real local HTTP and real bare Git state
are exercised; the only external substitute is the LL2 service/Pages observation.

R3 footer field contract was independently checked against the official
[development pad instance documentation](https://lldev.thespacedevs.com/2.3.0/pads/70/?format=api):
`pad.country.alpha_2_code` / `alpha_3_code` are supplied country codes;
`pad.location.name` is a separate site/location context from `pad.name`.
The source explicitly uses `??` / `???` for an unknown jurisdiction; those
placeholders map to null instead of an invented code. Tests author NZ/USA and
New Cosmodrome under unknown9999/77777 IDs; they are contract vectors, not
a current geographic/source recording. This documentation read makes no
production schedule call, global coverage or freshness qualification.
