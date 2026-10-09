# Test Results — grubForge v2.2.0

*2026-10-08 · the KognogOS test desktop (Sway, three screens). Matrix: [20261008 - Test Matrix for grubForge v2-2-0](20261008%20-%20Test%20Matrix%20for%20grubForge%20v2-2-0.md). Issues: F-6 #38 · F-7 #39 · #40.*

## 1 · Automated (Claude)

- `python -W always -m unittest discover -s tests` on forgekit 0.10.0: **83 + 25 script checks tests pass**, warnings as in the changelog. ✅
- Every fix in this version was also checked the other way: taken out once, its test seen failing, put back. ✅

## 2 · Javier's runs, inside hypeForge Settings (Boot Menu page), from the source folders (`scripts/try-unreleased.sh`)

Three runs on 2026-10-08, free-form rather than row by row:

1. **Afternoon, the first look:** the underlined letters weren't all shortcuts, Help had no number, "1-N screens" was confusing, Q still quit inside Settings, Try/Save showed everywhere (displayForge), History's numbers jumped into its sub-pages (nogForge), "Boot menu" should be "Boot Menu". → all fixed in this version.
2. **Evening, the second look:** "bottom bar, awesome!". A menu opened by its number didn't close on the second press; the open menu wasn't lit; letters should follow one rule (the first letter, else the next free one); About and License (then Keys and the Manual too) belonged in the work area, not windows. → fixed in forgekit 0.10.0, picked up here.
3. **Evening, the third look:** the page's own highlight stayed lit while Help or History was open. → fixed; Javier: **"perfect!"**

## 3 · On the installed package ✅

The packages were built locally from the signed GitHub release (`makepkg`: checksum and signature pass, the tests inside the build pass), installed through nog (`hypeforge/scripts/install-local-builds.sh`, forgekit first), and Javier ran the apps from the launcher's hypeForge Settings on 2026-10-08: **"all perfect!"** Then the AUR push, forgekit first.

| Rows | Result |
|---|---|
| The matrix's rows for Javier, on the installed package | ✅ 2026-10-08 · "all perfect!" |
