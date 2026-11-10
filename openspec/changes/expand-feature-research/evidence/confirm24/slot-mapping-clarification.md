# Slot-mapping clarification before screening release

The original reviewer schema described row-major physical order. The user requirement is to preserve four configurable logical field identities and values; different reading routes are an intended research axis. Before candidate screening/source freeze and before either packet is released, the author explicitly clarified that row-major is not a universal product constraint. The reviewer accepts this correction to the reviewer-added assumption.

The payload fields array identifies immutable logical slots. A candidate may declare a row-major, column-major or other explicit logical-slot-to-position mapping as part of its frozen layout grammar. The independent spatial audit must compare the observed positions/roles/values against that mapping, rather than infer DOM order or impose one global row-major ordering. A mapping cannot omit, duplicate or relabel a configured role/value, and cannot be changed after confirmation freeze.

No screen/confirm scene, ID, label, number, coordinate, state or oracle slot identity was changed. The initial seals and complete original packet files are retained under each packet's initial-seal directory. Only explanatory schema/protocol metadata is amended before release. This is not a new holdout or a repair of observations.
