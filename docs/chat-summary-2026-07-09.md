# Chat Summary - 2026-07-09

## Scope of This Session
This summary captures all work completed in this chat up to now for the AI Crypto Advisor project.

## What Was Created
- Added roadmap document: `docs/roadmap.md`.
- Added security rule file: `.cursor/rules/security-mvp-baseline.mdc`.

## What Was Updated
- Updated `.cursor/rules/mvp-delivery-standards.mdc`.
- Updated `.cursor/rules/backend-api-conventions.mdc`.
- Updated `.cursor/rules/frontend-mvp-conventions.mdc`.
- Updated `.cursor/rules/testing-and-commit-gates.mdc`.
- Updated `.cursor/rules/skill-evolution-workflow.mdc`.
- Updated `.cursor/skills/crypto-mvp-execution/SKILL.md`.
- Updated `.cursor/skills/commit-helper/SKILL.md`.

## Main Decisions and Direction
- Execution should follow a roadmap-first approach from `docs/roadmap.md` (Phase 0 to Phase 7).
- Work should be split into small, explicit, testable slices for weaker coding models.
- Model routing was defined:
  - GPT-5.5 for backend/data/services/routes/tests.
  - Composer for UI pages/components with contract-first prompts.
- Security baseline was formalized as an always-applied rule.
- Python backend workflow now enforces project-local virtual environment usage (`.venv`).

## Roadmap Highlights
- Core flow order:
  1. Project skeleton
  2. Data layer
  3. Auth
  4. Onboarding
  5. Providers + dashboard aggregation
  6. Feedback voting
  7. Frontend integration
  8. Hardening and delivery
- Dashboard must support partial section success with resilient fallbacks.
- Every slice must have explicit files, contract, test, and checkpoint.

## Security Baseline Added
- Password hashing and server-side session requirements.
- Session cookie and expiration policy.
- Input validation and output safety constraints.
- Authorization by session-scoped user identity only.
- SQL/query safety and secret-handling rules.
- Security-focused negative tests.

## Environment Rule Added
- Backend work must use a local `.venv`.
- Create with `python -m venv .venv`.
- Activate in PowerShell with `.venv\\Scripts\\Activate.ps1`.
- Install/test backend dependencies only inside active `.venv`.

## Current Status
- Docs/rules/skills are now aligned with architecture and roadmap.
- No application code implementation has started yet.

## Suggested Next Step
- Start roadmap implementation with `P0-S1` (backend bootstrap) using the new slice template and test gate rules.
