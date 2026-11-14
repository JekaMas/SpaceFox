# Contributing to SpaceFox

Issues and pull requests are welcome. Describe the observed problem or proposed change, the affected device or data when relevant, and how to reproduce it. Remove credentials, personal health values and family information from reports and screenshots.

Work from a current checkout and read [AGENTS.md](AGENTS.md), the applicable [project workflow](docs/PROJECT_WORKFLOW.md) and the selected OpenSpec change. Keep product requirements in that change and its `tasks.md`; distinguish browser, native simulator, hosted service and physical-device evidence. For a substantial change, document the behavior, relevant checks and their limitations, then review and repair the result. Keep valid prior test receipts unless an actual semantic input changes. The [SDD quickstart](docs/SDD_WORKFLOW.md) explains the public checkout's optional upstream workflow reference and does not assume a bundled submodule.

Run checks relevant to the changed behavior and report exact commands and results in the pull request. Python, Node, OpenSpec and Garmin SDK requirements vary by task; use already available tools and document missing prerequisites. Do not commit private signing keys, tokens, personal data or generated credentials. Code changes do not authorize publishing feeds, releasing packages or submitting to Garmin.

Original project code and specifications use [MIT](LICENSE); preserve the separate [third-party notices](THIRD_PARTY_NOTICES.md) and source attributions.
