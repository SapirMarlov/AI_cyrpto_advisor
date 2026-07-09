---
name: chat-summary
description: Summarize completed chat work into docs with clear decisions, changed files, and next steps. Use when the user asks to summarize progress, decisions, or outputs from one or more chats.
disable-model-invocation: true
---

# Chat Summary Skill

## Use This Skill When
- The user asks to summarize work done in the current chat.
- The user asks for a recap across recent chats.
- The project needs a written progress checkpoint in `docs/`.

## Output Target
- Create a summary file in `docs/` with date in filename:
  - `docs/chat-summary-YYYY-MM-DD.md`
- If a file for the same date already exists, append a new section instead of creating duplicate files.

## Required Summary Sections
1. Scope of session/chat.
2. Files created.
3. Files updated.
4. Main decisions made.
5. Roadmap or architecture alignment changes.
6. Rules/skills/process changes.
7. Security and environment policy updates (if any).
8. Current status and next recommended step.

## Writing Rules
- Keep language simple and direct.
- Prefer bullet lists for changed files and decisions.
- Do not include sensitive data, tokens, or secrets.
- Keep statements factual and tied to completed work only.
- Do not claim tests passed unless tests were actually run.

## Project-Specific Notes
- For this project, always mention:
  - `docs/roadmap.md` alignment status.
  - model routing policy (GPT-5.5 backend, Composer UI) when relevant.
  - security baseline and `.venv` requirements if touched in the chat.

## Quality Check Before Finish
- Verify all referenced files actually exist.
- Ensure the summary reflects only work completed in chat.
- End with one concrete next step.
