# Publisher cutover repair

Push run 43976206176 failed before deployment: its sparse partial checkout timed out in `git ls-tree -r -l HEAD`, while the earlier 0.2.2 dispatch 43974082510 showed the same failure. The sparse input list also omitted the new `watch_snapshot.py`. No hosted snapshot or phone result follows from either run.

The publisher now enumerates Git tree identities without resolving every blob size and streams only actual candidate files before confirming their Git identity a second time on a stable read. The sparse checkout lists the snapshot module. The source-fence tamper tests and the tree identity discriminator pass; the actual sparse source-fence test passes with 756 catalog inputs and four Git operations. The affected phone transport batch passes 8/8. The signed watch export retains source 452ccabc and is not compiled from this host-only follow-up. Actual GitHub Actions and public HTTPS readback remain required separately.
