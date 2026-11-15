The immutable raw/provider corpus and historical output are unchanged. The old
UI harness expected nine countdown-word keys that the current numeric-only face
no longer renders; the old three affected checks reproduced two failures and one
error in `old-tests-reproduction.log`. The first full twelve-test run had the
same totals (two failures, one error); its tool output was truncated, so it is
not presented as a complete raw log. The repaired three targeted checks passed
in `current-tests.log`. They verify the historical nine retained strings as an
exact historical superset and check the current empty face-word set, real
referenced menu strings and a menu mutation separately. No new provider capture
or five-language SDK execution occurred. `prior-test.py` is the exact old test.
