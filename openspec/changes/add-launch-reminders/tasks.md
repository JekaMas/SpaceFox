# Tasks

## 1. Feasibility

- [x] 1.1 Investigate Garmin notification, background and quiet-state APIs; preserve primary sources and limitations in [FEASIBILITY.md](evidence/FEASIBILITY.md).
- [x] 1.2 Compile and run an isolated FR165 SDK context probe; retain source and results in [RESULT.md](evidence/sdk-probe/RESULT.md).

## 2. Requested behavior — blocked

- [ ] 2.1 Establish a viable authorized architecture that meets the full requested cadence, physical vibration and quiet-state contract; document evidence and update design before implementation.
- [ ] 2.2 Create the requirement-to-test DAG and discovery record, then implement the exact reminder behavior and production settings; verify native boundaries, persistence, suppression and localization.
- [ ] 2.3 Verify physical watch and phone behavior, independent review and release only after all requested behavior and applicable gates have passed.

Resume: no production behavior, permission or release was changed. A 5-minute background lower bound and lack of a documented vibration control or dependable one-minute screen-off callback prevent claiming the requested contract. The result of 1.1–1.2 is a feasibility finding, not a passed implementation. A limited notification option requires a separate explicit product decision.
