# Application Engineer Implementation Plan

**Goal:** Build the application portion of AI-DMC with an explicit temporary mock.

**Architecture:** Next.js frontend, FastAPI backend, PostgreSQL, local file storage. Pipeline and taxonomy owned by Person 1 are consumed through an adapter; backend-local demo fixtures make application development independent.

**Tech Stack:** TypeScript, Next.js, Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Docker Compose.

The user approved the design on 31 October 2026. Execute backend and frontend in parallel with the executing-plans workflow, then review their interface and validate together. Do not start real pipeline work or claim deployment/review complete.

## Tasks

- [x] Foundation: .gitignore excludes real documents, local storage and secrets. Copy the supplied design skill. Compose starts db/backend/frontend; examples contain development values only.
- [x] Database: backend/app/models plus Alembic migration create the five defined tables, seed two dummy lecturers and one admin, enforce append-only audit writes.
- [x] Authentication: Argon2 passwords, expiring JWT, protected routes, audited login. Test missing/invalid token and separate lecturer access.
- [x] Upload: stream and validate each file, limit 20 MB, SHA-256 deduplication, UUID storage, safe duplicate responses. Test accepted formats and invalid/oversized inputs.
- [x] Pipeline adapter: explicit mock high/low/failure scenarios; validate result and map fields/lecturers. Test confidence at exactly 0.85, low score and failure.
- [x] Document API: list/filter/detail/file with ownership or lecturer links and confidential owner restriction. Test cross-account reads/mutations, correction snapshots and export admin restrictions.
- [x] Frontend: four connected pages, shared design tokens and navigation, upload polling, review/correction/preview, archive filters, delayed approve/reject for undo. Run TypeScript check and production build.
- [x] Wireframes: save four desktop and four mobile PNG layout references under docs/wireframe; these are design references rather than screenshots of the application.
- [x] Integration: inspect shared API contract, run meaningful backend tests and frontend build, check 375/1280 px if browser runtime is available, record real limitations.
- [x] Delivery: root/backend/frontend READMEs, one-page lecturer guide, checklist distinguishing local implementation from external handoffs.

## Verification commands

Backend environment setup and tests are documented in backend/README.md; run its pytest command. PostgreSQL migration and compose validation require Docker, which is not installed at initial inspection. Do not report those checks as passed until run against PostgreSQL.

Frontend: `npm ci`, `npm run build`, and the typecheck command defined in frontend/package.json. Inspect screenshots and confirm keyboard focus and no horizontal overflow at 375 and 1280 px when browser tooling permits.

## External dependencies

Real taxonomy and process_document(): Person 1. Contract changes, partner review, merge, server deployment and lecturer trials remain external gates. No GitHub operations or messages to others are authorized by this plan.
