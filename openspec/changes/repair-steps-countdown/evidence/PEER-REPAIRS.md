# Bounded independent repairs

## Full sample read ownership

Confirmed `Fitness.sample` read ActivityMonitor even with a valid selected Garmin ID2 and then overwrote the step total. The selected-fitness oracle expected that duplicate I/O. The exact actual SDK RED is retained in `peer-steps-read-first-red.log`.

Full sample now takes the selected complication first. ActivityMonitor is read once only when steps are missing or calories require it. Its failure cannot erase valid complication steps. Callback sampling keeps the existing `sampleSteps` path. Directed production-owner assertions cover current42, zero0, null fallback7, shared steps/calories fetch and calories error with valid zero steps. The independent 64-seed oracle now counts fallback reads from model inputs after each event. The cold-LOW assertion’s prior two reads included the eliminated duplicate after complication41. Its preserved RED is separate from the product failure; the corrected expectation is one original cold fallback read.

## Fallback stale signal

The fallback countdown had the independent arrow and hold pause but lacked stale dots. A single `SceneAod.staleMark` implementation now supplies existing normal ACTIVE/LOW dots and fallback dots. Existing normal coordinates are unchanged. New fallback checks compare effect counts against a no-indicator world-map baseline in both modes, then require stale-only dots, hold two lines and combined reschedule/hold eight lines. The first test adapter lacked getWidth/getHeight; its error is preserved. The subsequent test incorrectly counted map geometry as cue lines; its accounting RED is also preserved before correction. Neither harness error is represented as a product counterexample.

## Actual affected results and metadata

Both FR165 profiles pass stepsCountdownBatch, generatedFitnessOwners and coldLowAcquiresOneFieldSnapshot. The batch includes the directed ownership/cue controls and12seeds/576events; the fitness generator has64seeds/3720events with after-event/end assertions. Current five-primary source was genuinely recompiled and all five affected selectors passed after the production changes. NativeID is c1c2ebd4. Original author raw/qualification remains immutable at d3ba5ef7. The first qualification attempt collided with a concurrent runtime compile in their shared private generated-output directory; isolated output resolved it. Full first compile error remains preserved. No native SDK installation or broad campaign was added.
