# Design

Model independent external OS mode changes without directly synchronizing the SUT. Deliver show, hide, enter-sleep, exit-sleep and frame callbacks through the real SpaceFoxView with fake ports. Compare an independent model after each event and at trace end. The required first-wake witness begins with LOW show without enter-sleep, changes the OS to HIGH, then dispatches exit-sleep; visible ACTIVE mode and a prompt useful-frame request must follow. Duplicate/hidden callbacks must respect visibility. Apply the same property to the historical guard as a test-only mutation and retain its failure, then the unchanged production source must pass.

Fake ports, coverage dispositions, seeds and full command results are recorded with the runs. Simulator execution is not a physical tap or wake-latency observation.
