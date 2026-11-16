# Memory and resource audit

Start with [the final report](REPORT.md). It distinguishes source findings, exact retained simulator measurements, new offline host measurements and open physical metrics.

- [Plan and progress journal](AUDIT.md)
- [Native ownership, release and hot paths](NATIVE.md)
- [Publisher, external requests and host costs](HOST-AND-REQUESTS.md)
- [Resources, research and engineering tools](RESOURCES-AND-TOOLS.md)
- [Every tracked file and its disposition](FILE-INVENTORY.csv)
- [Source review method and notes](SOURCE-REVIEW.json)
- [Native resource sizes and metadata](RESOURCE-INVENTORY.csv)
- [Every engineering command](TOOLS.md)
- [Per-function Python resource calls](PYTHON-RESOURCE-SCAN.json)
- [Supporting script resource sites](SUPPORTING-SCRIPT-SCAN.json)
- [Offline host measurement](HOST-MEASUREMENT.json)
- [Geography cache release measurement](CACHE-RELEASE-MEASUREMENT.json)
- [Measurement environment and source hashes](MEASUREMENT-ENVIRONMENT.json)
- [Artifact consistency check](AUDIT-CHECK.json)

This is analysis of fixed main `943f320c`, version 0.1.18. It does not change native behavior, run the deployed updater, spend provider/model API credits or publish a release.
