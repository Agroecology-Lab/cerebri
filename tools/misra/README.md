# MISRA C:2012 via cppcheck

Modeled on IMProject/IMUtility's `make misra` target
(https://github.com/IMProject/IMUtility/blob/main/Makefile), adapted for a
Zephyr/west build instead of a flat host-compiled library:

- They scan `Src` directly with `-I` flags (no build system to speak of).
- We instead point cppcheck at a `compile_commands.json` from a real west
  build, because cerebri's C is guarded by devicetree-generated headers and
  Kconfig defines that plain `-I` scanning can't resolve — without it,
  cppcheck either drowns in "unknown macro" noise or silently skips
  `#ifdef CONFIG_...` branches.

## The rule-text gap (same one IMUtility has)
`cppcheck --addon=misra` only ships rule *numbers* — the rule *text* is
MISRA/HORIBA MIRA copyrighted, so cppcheck can't bundle it. IMUtility's
Makefile runs `--addon=misra.py` with no `--rule-texts` at all for exactly
this reason: passing `--rule-texts=<path>` to a file that doesn't exist
makes cppcheck **error out**, not just print numbers instead of prose. Do
not add a `--rule-texts` flag to the CI job until `tools/misra/rule-texts.txt`
actually exists.

To get one: your org needs a MISRA C:2012 license
(https://misra.org.uk), then run cppcheck's own extractor against your PDF —
`python3 <cppcheck-src>/addons/misra.py --generate-rule-texts <pdf>` — and
commit the output at `tools/misra/rule-texts.txt`. It's gitignored below on
purpose; don't commit a copyrighted rule-text file to a public fork.

## What the CI job actually does
1. `west build -b mr_canhubk3/s32k344 app/b3rb -- -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`
   — one representative board/app, not the full twister matrix. Fast, and
   MISRA is a structural/style check — one concrete Kconfig configuration
   is an honest compromise, not full coverage of every board × app combo.
2. `cppcheck --project=build/compile_commands.json --addon=misra`, scoped
   with `-i zephyr -i modules -i build` so only `app/`, `drivers/`, `lib/`,
   `include/cerebri` are actually reported on — same idea as IMUtility's
   `-iTests/Unity` for their vendored test framework.
3. Report-only for now (`--error-exitcode=0`) — the codebase has never been
   through this, so day one would be all red. Flip to `1` once triaged.

## `.gitignore` additions
```
tools/misra/rule-texts.txt
```
