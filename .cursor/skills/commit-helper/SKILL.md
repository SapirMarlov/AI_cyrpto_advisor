---
name: commit-helper
description: Prepare safe, focused commits with one logical change per commit. Use when staging changes, splitting work into commits, writing commit messages, requesting commit approval, or validating commit readiness.
disable-model-invocation: true
---

# Commit Helper

## Use This Skill When
- The user asks to commit changes.
- A task is complete and ready for commit.
- Commit message quality, staging scope, or commit splitting needs review.

## Before Committing
1. Run `git status` and `git diff` to see all changes.
2. Group changes into **logical units** (one concern each).
3. If multiple units exist, propose a commit plan and split before committing.
4. Confirm tests for affected areas pass before each commit.

## Splitting Large Work
Split into separate commits when changes mix:
- schema vs routes vs UI vs tests
- unrelated features or roadmap phases
- refactors mixed with behavior changes

Suggested order for a full slice:
1. `chore` or schema/migration
2. `feat` / `fix` backend logic and routes
3. `feat` / `fix` frontend
4. `test` coverage for that slice

Stage with explicit paths (`git add backend/...`) — avoid `git add .` when the tree is mixed.

## Message Format
Follow `.cursor/rules/git-workflow.mdc`.

**Subject:** `<type>: <imperative summary>` (max 72 chars)

**Body:** Add when the why, trade-off, or reviewer context is not obvious from the subject. Keep it to 1–3 sentences or a few bullets.

```
fix: handle CoinGecko timeout with dashboard fallback

Return cached prices when the provider exceeds the 5s timeout so the
dashboard still renders partial market data.
```

## Scope and Safety
- One logical change per commit.
- Do not include unrelated files.
- Do not commit secrets or credential files.
- If tests fail, fix or report before committing.
- Ask user permission before committing unless they explicitly requested it.
- After commit: run `git status` and `git log -1` to verify.

## Types
- `feat` — new behavior
- `fix` — bug fix
- `test` — tests only
- `refactor` — behavior-preserving restructure
- `chore` — tooling, deps, config
- `docs` — documentation only
