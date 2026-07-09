---
name: crypto-mvp-execution
description: Execute the AI Crypto Advisor MVP quickly with clean architecture, tests, and strict scope control. Use when implementing onboarding, dashboard sections, API integrations, feedback loops, or deployment-ready increments for this project.
disable-model-invocation: true
---

# Crypto MVP Execution

## Use This Skill When
- The task is part of the AI Crypto Advisor MVP.
- The user asks to implement features, wire APIs, or prepare deployment.
- Trade-offs are needed to finish in 1-2 work days.
- The team/model needs strict roadmap-driven slices to reduce errors.

## Mission Checklist
- Core user journey works end-to-end:
  1. Signup/Login
  2. First-login onboarding quiz saved to DB
  3. Daily dashboard with:
     - Market News
     - Coin Prices
     - AI Insight of the Day
     - Fun Meme
  4. Thumbs up/down feedback persisted per section

## Execution Rules
- Build smallest complete slice first, then expand.
- Keep folder structure minimal and clean.
- Add code only when required for architecture clarity.
- Keep method names in simple English.
- Prefer free APIs and include safe fallback responses.
- Follow `docs/roadmap.md` phase order unless the user explicitly reprioritizes.
- For each slice, define before coding:
  1. Exact files to touch
  2. API/data contract
  3. Acceptance test
  4. Slice checkpoint

## Model Routing (Required)
- Use GPT-5.5 for backend, repositories, services, routes, and tests.
- Use Composer for UI pages/components and styling updates.
- Before any Composer UI generation, provide contract-first prompt inputs:
  - endpoint and payload shape
  - component props
  - loading/empty/error states
  - redirect/guard behavior

## Slice Template
- `Slice ID`: phase-slice key (example: `P2-S2`)
- `Goal`: single outcome
- `Files`: exact create/edit list
- `Contract`: request/response shape and validation rules
- `Tests`: unit/e2e checks to add or update
- `Checkpoint`: short pass condition

## Quality Gate
- Add or update unit tests and e2e tests for changed behavior.
- Run tests and fix failures before marking a task done.
- Highlight missing test coverage explicitly if blocked.
- Include negative/error-path tests for auth and provider failures.

## Commit and Collaboration
- After every big change, ask for user permission before committing.
- Use short informative commit messages (max 180 chars).

## Save Gotchas
- Record gotcha moments during implementation:
  - API limits and downtime behavior
  - Auth/session pitfalls
  - Data-mapping edge cases
  - Flaky e2e conditions

## Delivery Priority
- Prioritize MVP completion in 1-2 work days over optional improvements.
- Defer bonus ideas to a clear "next" list unless requested now.
