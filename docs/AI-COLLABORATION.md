# 🤝 Building grubForge with AI — how we preserve context

grubForge is a **human + AI collaboration** (Javier `jetomev` + Claude/Anthropic).
A recurring question from other developers is: *"How do you keep an AI
collaborator on track when its context keeps getting compacted?"* This page is
the honest answer.

## The problem: context loss from compaction

An AI coding assistant has a finite working memory (a "context window"). In a
long session, the tooling automatically **summarizes older conversation into a
shorter digest to free up space** — and that digest is lossy. Exact code
snippets, specific decisions, and edge cases discussed hours earlier can get
blurred or dropped. That is *context loss from compaction*.

For most projects that's a nuisance. For a tool that writes your **bootloader
configuration**, an AI that silently "forgets" where things stood could regress
a fix, re-open a closed decision, or lose a test finding. So we don't try to
prevent compaction — we assume it *will* happen and design around it.

## The core principle

> **The AI's memory is treated as disposable. Every durable decision lives in an
> artifact outside the conversation.**

Nothing important is trusted to recall. If it matters, it's written down
somewhere permanent, and every session *starts* by reading those artifacts
instead of relying on what the AI "remembers."

## The four mechanisms

| Artifact | What it holds | When it's used |
| --- | --- | --- |
| **Session handoff logs** — `grubForge - (N) Part M.md`, each ending in a mandatory `## Next-session handoff (read this first)` section | Exact next step, open findings, watch-fors, what's installed/staged | Written at the end of every session; **read first** at the start of the next |
| **Persistent project + workflow notes** | Release state, conventions, the collaboration rules themselves | Reloaded every session, independent of what got compacted |
| **Committed test artifacts** — `testing/` matrices + results, one file per release cycle | Every test's expected/actual, each `Fxx` finding, dogfood results | The permanent record that a change was verified |
| **GitHub Issues, per finding** | One issue per `Fxx` finding, closed by the commit that fixes it | Makes the test→fix→verify loop auditable by anyone |

Decisions also land in **git history** (co-author trailers on every commit) and
the **README changelog**.

## The session lifecycle

1. **Start** — read the latest handoff log's `## Next-session handoff` section
   *before* anything else, then reconcile it against the notes and the actual
   repo/issue state and surface any drift. (The handoff was accurate at session
   close; memory and code drift — the handoff wins.)
2. **Work** — iterate at ToDo granularity; keep the README, GitHub surface, and
   issues in sync as changes land.
3. **End** — write a new handoff log capturing the day's decisions *and* a fresh
   `## Next-session handoff` block, so the next session (with a fully compacted
   or blank memory) can pick up exactly where this one stopped.

## Why this doubles as documentation

Publishing the test matrices, the per-finding issues, and this page is
deliberate. grubForge's goal isn't only a working GRUB TUI — it's to show that
a human + AI pair can produce **carefully engineered, verifiable software**, not
vibe-coded output. The context-preservation discipline is part of that evidence.

---

*Questions about the workflow are welcome — open an issue.*
