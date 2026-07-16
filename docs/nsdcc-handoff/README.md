# NSDCC Workflow Frontend — Implementation Handoff

This is the master handoff for completing the NSDCC physical-document workflow UI.
Read this file fully before touching code, then read the PRD for the phase you are
implementing (`phase-4-*.md` → `phase-5-*.md` → `phase-6-*.md`, in order).
`backlog-for-exploration.md` lists known issues and product gaps you should be aware
of but NOT fix unless a PRD says so.

## 1. What this product is

EDMS/IDMS is a paperless-ngx fork (package renamed `idms`, v3.0.0) sold as a document
management system. The NSDCC feature tracks *physical* documents: the CEO's office
receives paper mail, the PA scans and uploads it, Registry serialises/categorises and
assigns it, staff action it (possibly delegating), and Registry files it. Reference
reading, in priority order:

1. `docs/nsdcc-workflow.md` — backend implementation guide (models, endpoints, permissions)
2. `docs/nsdcc-workflow-issues.md` — the original 9-issue plan with full specs
3. The PRDs in this folder — these SUPERSEDE the GitHub issue bodies where they differ
   (notably: GitHub issue #45's body is a copy-paste duplicate of #44 — ignore it;
   `phase-5-workflow-detail.md` is authoritative)

## 2. Current state (as of 2026-07-14)

Three stacked PRs are open, reviewed, CI-tested, and live-verified. None are merged;
merging requires the repo owner's explicit approval. Merge order matters.

| PR | Branch | Base | Contents |
|----|--------|------|----------|
| #47 | `workflow-api-service` | `main` | Issue #40: TS interfaces (`src-ui/src/app/data/nsdcc-workflow.ts`) + `NsdccWorkflowService` (12 endpoints, 13 Jest tests). Backend contract fixes: inbox includes `overdue` status; list serializer gained `instruction`, `assigned_by`, `document_type`; N+1 prefetch guards; first backend test suite (`src/nsdcc_workflows/tests/`, 11 tests). CI repairs: `pull-requests: read` in both workflows, regenerated `uv.lock` (paperless-ngx→idms rename) and `pnpm-lock.yaml`. |
| #48 | `workflow-role-guard` | `workflow-api-service` | Issue #41: `WorkflowRoleGuard` (`src-ui/src/app/guards/workflow-role.guard.ts`, 8 Jest tests). Backend: `UiSettingsView` now returns `user.group_names` and `settings.nsdcc_groups` (the env-configured role→group-name mapping). Registered in `main.ts` providers. No route uses the guard yet. |
| #49 | `workflow-inbox-page` | `workflow-role-guard` | Issue #43 + part of #42: `WorkflowInboxComponent` + `workflow/inbox` route + `workflow/document/:id` → `documents/:id` redirect (placeholder until phase 5). Live UI evidence in `docs/assets/pr-workflow-inbox/`. |

**Your work starts from the `registry-dashboard` branch** (this branch), which is cut
from `workflow-inbox-page`. Each phase = one PR, based on the previous phase's branch
(continue the stack). Retarget bases to `main` as earlier PRs merge.

Remaining GitHub issues (all assigned): #44 registry dashboard (+ close #42), #45
workflow detail, #46 initiate modal, #50 sidebar navigation + upload hook.
Phase→issue mapping: Phase 4 = #44 + #42-completion + sidebar half of #50;
Phase 5 = #45; Phase 6 = #46 + upload-hook half of #50.

## 3. Architecture crash course

### Backend (`src/nsdcc_workflows/`) — complete, do not modify unless a PRD says so

- Models: `DocumentWorkflow` (1:1 with `documents.Document`, related name `nsdcc_workflow`),
  `DocumentWorkflowAction` (append-only log, related name `actions`),
  `DocumentWorkflowAttachment` (related name `attachments`).
- Statuses: `received → pending_action → reassigned → actioned` (+ `overdue`, set by a
  nightly Celery task). Confidentiality: `public|internal|confidential|restricted`.
- 12 endpoints under `/api/nsdcc-workflow/` — see the table in `docs/nsdcc-workflow.md`.
  `{id}` in URLs is always the **document** id, not the workflow id.
- Roles are Django auth groups; names configurable via `PAPERLESS_NSDCC_PA_GROUP` /
  `_REGISTRY_GROUP` / `_GENERAL_STAFF_GROUP` (defaults PA/Registry/GeneralStaff).
  Superusers bypass everything. `python manage.py create_workflow_groups` creates them.
- List endpoints (`inbox/`, `registry/`) return plain arrays (NOT paginated `Results<T>`)
  of the list shape; detail returns the full nested object.

### Frontend (`src-ui/`, Angular 21, standalone components, Bootstrap 5 + ng-bootstrap)

- Data layer: `src/app/data/nsdcc-workflow.ts` — all interfaces/enums/request types.
  `src/app/services/rest/nsdcc-workflow.service.ts` — `NsdccWorkflowService`, inject it
  with `inject()`. Never touch `workflow.service.ts` (that is Paperless's separate
  automation engine).
- Role guard: `src/app/guards/workflow-role.guard.ts`. Use on routes via
  `canActivate: [WorkflowRoleGuard], data: { requiredGroups: ['Registry'] }` — values are
  the DEFAULT group names; the guard resolves env-renamed deployments through the
  `nsdcc_groups` mapping automatically. Copy its group-resolution pattern anywhere else
  you need a role check (e.g. sidebar visibility).
- Current user: `SettingsService.currentUser` (`User` interface has `group_names?: string[]`,
  `is_superuser`). Settings registry key: `SETTINGS_KEYS.NSDCC_GROUPS`.
- Existing reference component: `src/app/components/workflow/workflow-inbox/` — copy its
  conventions (standalone, `PageHeaderComponent`, `CustomDatePipe`, `$localize` on all
  user-facing strings, `LoadingComponentWithPermissions` base, `ToastService` errors,
  `@for` with `track`, status→badge map).
- Routing: `src/app/app-routing.module.ts`, all pages are children of the
  `AppFrameComponent` shell route; every route sets `data.componentName`.
- Status badge conventions (keep consistent): `pending_action`→`bg-primary`,
  `reassigned`→`bg-warning text-dark`, `overdue`→`bg-danger`, `received`→`bg-secondary`,
  `actioned`→`bg-success`. Use `status_display` for labels. Note: `bg-primary` renders
  GREEN under the IDMS theme — that is correct/intended.

## 4. Conventions and hard rules

- Branch names: short, plain (`registry-dashboard`, `workflow-detail`, `initiate-modal`).
- Commits: lowercase conventional (`feat:`, `fix:`, `test:`, `docs:`, `ci:`, `perf:`,
  `style:`). Commit everything you do, in reviewable units.
- One PR per phase, stacked as described above. NEVER merge a PR — the owner merges.
- Every PR must include before/after screenshot evidence, committed under
  `docs/assets/pr-<branch>/` and linked from the PR body (repo is private; raw links
  don't render inline, blob links are fine).
- Copilot auto-reviews PRs. Address its comments (or rebut with reasons), reply on each
  thread, and resolve the threads.
- Scope discipline: this repo is shared. Touch only what the PRD lists. Match the
  existing lint/format style (frontend: prettier, no semicolons, single quotes;
  backend: ruff with single-import-per-line).

## 5. Environment, testing, verification (Windows host!)

- **Frontend tests**: run from `src-ui/`: `npx jest <pattern>`. Full suite is green.
  Lint: `pnpm run lint`.
- **Backend tests CANNOT run natively on Windows** (`uv.lock` pins linux/darwin;
  `psycopg-c` needs a native build). CI runs them (`pytest`, job "Backend Tests") —
  that is the green-run source. Write tests following `src/nsdcc_workflows/tests/test_api.py`.
- **CI noise to IGNORE (pre-existing, team-aware)**: the `Lint (prek)` job fails
  repo-wide (`--all-files` against old violations); `test_index` and `test_api_schema`
  backend failures pre-date this work. Only address CI feedback caused by YOUR diff.
- **Local live verification** (do this before each PR):
  1. Build an image from your branch — MUST use git archive because the working tree is
     CRLF and breaks the image (`exit 127` on shebangs):
     `git -c core.autocrlf=false archive <branch> | docker build -t edms-local:stack -`
  2. `docker compose up -d` in `docs/nsdcc-handoff/dev-env/` (redis + webserver, sqlite,
     port 8000, admin/admin).
  3. First boot only: `docker exec edms-dev-webserver-1 python3 manage.py create_workflow_groups`,
     then `docker cp dev-env/seed_demo.py edms-dev-webserver-1:/tmp/ &&
     docker exec edms-dev-webserver-1 sh -c "python3 manage.py shell < /tmp/seed_demo.py"`
     (prints fresh API tokens), then grant baseline perms — see `dev-env/README.md`.
  4. Demo users (password `demo1234`): `pa_office` (PA), `registry_ann` (Registry),
     `jmwangi` + `kotieno` (GeneralStaff). Superuser `admin`/`admin`.
  5. Headless screenshots without interactive login: temporarily set
     `PAPERLESS_AUTO_LOGIN_USERNAME=<user>` on the webserver, `docker compose up -d`, then
     `chrome --headless --disable-gpu --hide-scrollbars --window-size=1440,900
     --virtual-time-budget=20000 --screenshot=<out.png> http://localhost:8000/<path>`.
     Remove the env var afterwards.
  - If Docker errors with "cannot find the pipe", Docker Desktop's engine died — relaunch
    `C:\Program Files\Docker\Docker\Docker Desktop.exe` and wait ~30s.

## 6. Definition of done, per phase

1. All acceptance criteria in the phase PRD demonstrably met.
2. Jest specs for every new component/behavior, run green locally; backend changes (if
   the PRD includes any) come with tests that pass in CI.
3. Live verification screenshots captured and committed; PR body written with a
   what/why/evidence structure.
4. Copilot review comments addressed and threads resolved.
5. No scope creep beyond the PRD + reviewer feedback.
