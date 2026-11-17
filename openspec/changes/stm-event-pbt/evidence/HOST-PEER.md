# Independent host review

Reviewed host author commit `640340f80859975e0cf562e32d969cc1f1ced6e6`: actual Publisher, GitState and Cloud transitions, input-derived independent model, fake service boundaries, per-event and end assertions, replay, required disposition counters, and per-thread isolated fixtures. This review is limited to the Python host owners; it is not native, live-network, hardware or 600-second campaign evidence.

The review repaired three evidence gaps before campaign:

* The runner had counted coordinator gaps toward productive time. The deterministic red control is `HOST-PEER-budget-red.log`; the runner now accumulates only successful trace execution time and separately reports wall elapsed.
* Forbidden-effect guards omitted filesystem metadata and nanosecond clock calls. The sentinel-only red control is `HOST-PEER-guard-red.log`; `HOST-PEER-guard-first.log` records the selected passing controls and four-owner threaded execution. Fake sentinel calls do not touch real services.
* The source model lacked explicit independent selected-launch/timing assertions and effective witnesses for started/unknown status and window/unknown timing. Retain `HOST-PEER-source-coverage-red.log` and `HOST-PEER-timing-coverage-red.log`; corrected controls and eight current source traces passed in `HOST-PEER-source-coverage-green.log`, `HOST-PEER-timing-coverage-green.log`, and `HOST-PEER-source-timing.log` (1,376 events, per-event selection assertions, zero forbidden effects). These synthetic witnesses do not establish all source precisions or provider integration.

The initial named-test invocation in `HOST-PEER-timing-coverage-green.log` used a wrong class name; the file was overwritten by the corrected passing invocation. No product failure is implied. Existing author receipts remain valid within their recorded inputs; the source generator changed, so the new source receipt applies instead. The four independent 600-second productive campaigns remain required and have not yet run.
