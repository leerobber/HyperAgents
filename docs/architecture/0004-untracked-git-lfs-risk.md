# 0004: Real Git LFS pointer files with no LFS tracking configured

**Status:** Needs attention — found, not resolved (can't verify remotely whether the real data exists)

## Context

The repo root has `outputs_os_parts.z01` through `.z08` plus
`outputs_os_parts.zip` (9 files). Each is a **real Git LFS pointer file**
(`version https://git-lfs.github.com/spec/v1`, a `sha256` oid, and a
declared `size`) — not the actual data.

## What was actually checked

- Each pointer declares `size: 2147483648` (exactly 2 GiB) — so this
  represents roughly **18 GB** of intended real data (a large output or
  dataset, split into 2 GiB volumes, named "outputs_os_parts").
- There is **no `.gitattributes` file in this repo** configuring LFS
  filters for these paths (or anything else).
- `git-lfs` is not installed on this machine, so `git lfs pull`/
  `git lfs ls-files` couldn't be run to check whether the real objects
  actually exist server-side.

## Why this matters

Without a `.gitattributes` `filter=lfs` rule, a normal `git add`/`git
commit` of a file that happens to *contain* LFS-pointer-formatted text
does not trigger a real LFS upload — it just commits that pointer text as
an ordinary small file. That means one of two things is true, and this
session's tools couldn't distinguish which:

1. LFS was configured correctly at some point (`.gitattributes` existed,
   `git lfs` was installed, the real 18 GB was actually uploaded to
   GitHub's LFS storage), and the `.gitattributes` rule was later lost
   (e.g. in a rebase, a `.gitignore`-only cleanup, or never committed to
   this branch) — the real data may still exist on GitHub's LFS backend
   and just needs the tracking rule restored.
2. The real data was never actually uploaded via LFS at all — these
   pointer files were generated (e.g. by a tool that always emits LFS
   pointer format) but never pushed through an actual LFS-aware git
   client — in which case the referenced 18 GB doesn't exist anywhere
   these pointers can resolve it from.

## Consequences / what's needed to resolve this

Requires access to a machine with `git-lfs` installed to run
`git lfs pull` (or `git lfs fsck`) against the real GitHub repo and see
whether the objects resolve — not something verifiable from this
investigation alone. If the data is confirmed gone, these 9 pointer files
are dead weight and should be removed or replaced with real content /
a real download step. If confirmed present, add a `.gitattributes` with
`outputs_os_parts.* filter=lfs diff=lfs merge=lfs -text` so future clones
and commits handle it correctly.
