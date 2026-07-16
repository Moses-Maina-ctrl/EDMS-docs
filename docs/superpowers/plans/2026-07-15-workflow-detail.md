# Workflow Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the workflow document redirect with a complete, role-aware workflow detail page and add the missing Registry summary write path.

**Architecture:** Keep the detail page as the workflow-state orchestrator and isolate assign, delegate, and mark-actioned form state in small modal components. Mutations return the updated workflow wherever the API already does so the page can replace local state without redundant requests; attachment upload appends its returned attachment and reports HTTP progress. The backend summary endpoint mirrors serialisation and reuses the existing comment action type.

**Tech Stack:** Django REST Framework, Angular standalone components, ng-bootstrap, ng-select, RxJS, Jest, Bootstrap 5, pngx-pdf-viewer.

---

### Task 1: Summary API contract

**Files:**
- Modify: `src/nsdcc_workflows/tests/test_api.py`
- Modify: `src/nsdcc_workflows/views.py`
- Modify: `src/nsdcc_workflows/urls.py`
- Modify: `docs/nsdcc-workflow.md`
- Modify: `docs/nsdcc-handoff/implementation-notes.md`

- [ ] Write backend tests proving GeneralStaff receives 403, Registry receives 200, the trimmed non-blank summary persists, and a `comment_added` action with `Summary updated` is recorded.
- [ ] Do not run backend tests natively on Windows; validate syntax/format locally and rely on the Backend Tests CI job for execution.
- [ ] Add `SummariseWorkflowView` with `IsRegistryOrAdmin`, the same document/workflow lookup shape as `SerialiseWorkflowView`, non-blank validation, persistence, action logging, and detail serialization.
- [ ] Register `PATCH documents/<int:pk>/summarise/` as `nsdcc-workflow-summarise` and add it to the endpoint table.
- [ ] Update the implementation notes, inspect the scoped diff, and commit as `feat: add workflow summary endpoint`.

### Task 2: Frontend data and service contract

**Files:**
- Modify: `src-ui/src/app/data/nsdcc-workflow.ts`
- Modify: `src-ui/src/app/services/rest/nsdcc-workflow.service.spec.ts`
- Modify: `src-ui/src/app/services/rest/nsdcc-workflow.service.ts`
- Modify: `docs/nsdcc-handoff/implementation-notes.md`

- [ ] Add a failing Jest spec expecting `PATCH /api/nsdcc-workflow/documents/:id/summarise/` with `{ summary }`.
- [ ] Run `npx jest nsdcc-workflow.service.spec.ts --runInBand` and confirm the failure is caused by the missing method.
- [ ] Add `SummariseWorkflowRequest` and the typed `summarise()` service method.
- [ ] Re-run the focused spec to green, update memory, inspect the scoped diff, and commit as `feat: add workflow summary client`.

### Task 3: Focused workflow form modals

**Files:**
- Create: `src-ui/src/app/components/workflow/workflow-detail/assign-modal/assign-modal.component.{ts,html,spec.ts}`
- Create: `src-ui/src/app/components/workflow/workflow-detail/delegate-modal/delegate-modal.component.{ts,html,spec.ts}`
- Create: `src-ui/src/app/components/workflow/workflow-detail/action-modal/action-modal.component.{ts,html,spec.ts}`
- Modify: `docs/nsdcc-handoff/implementation-notes.md`

- [ ] Write failing specs proving assign requires a user and preserves optional instruction/deadline, delegate requires a user and preserves optional comment, and action requires a non-whitespace comment while allowing an optional file.
- [ ] Run the three modal specs and confirm expected red failures.
- [ ] Implement standalone ng-bootstrap modal components. Load active users once through `UserService.listAll()`, render `first_name last_name (username)` labels in ng-select, and close only with validated payloads.
- [ ] Re-run the modal specs to green, update memory, inspect the scoped diff, and commit as `feat: add workflow action dialogs`.

### Task 4: Detail page rendering and access states

**Files:**
- Create: `src-ui/src/app/components/workflow/workflow-detail/workflow-detail.component.{ts,html,scss,spec.ts}`
- Modify: `src-ui/src/app/app-routing.module.ts`
- Modify: `docs/nsdcc-handoff/implementation-notes.md`

- [ ] Build a complete workflow fixture and write failing specs for the route, two-column page, header badges, deadline/overdue treatment, assignee/instruction/serial/summary/categorised sections, attachments, and chronological history with assignment transitions.
- [ ] Add failing role/status specs for PA, Registry, current assignee, unrelated staff, superuser, and actioned status.
- [ ] Add failing 404 and 403 specs: 404 renders a friendly linked panel; 403 shows the exact permission toast and redirects to `/dashboard`.
- [ ] Run the focused detail spec and confirm expected red failures.
- [ ] Implement the route and standalone page using `ActivatedRoute`, `NsdccWorkflowService`, `DocumentService.getPreviewUrl`, `SettingsService`, the configured NSDCC group mapping, `CustomDatePipe`, and `pngx-pdf-viewer`.
- [ ] Keep the PDF surface usable at desktop and stacked at narrow widths; keep the state panel sections visually distinct without introducing a new design system.
- [ ] Re-run the focused detail spec to green, update memory, inspect the scoped diff, and commit as `feat: add workflow detail page`.

### Task 5: Mutations and upload progress

**Files:**
- Modify: `src-ui/src/app/components/workflow/workflow-detail/workflow-detail.component.{ts,html,spec.ts}`
- Modify: `docs/nsdcc-handoff/implementation-notes.md`

- [ ] Add failing page specs for assign, delegate, action with optional pre-upload, serialise, summarise, categorise/uncategorise, standalone attachment upload, HTTP upload progress, success-state replacement, and backend error extraction (string or list).
- [ ] Run the focused spec and confirm expected red failures.
- [ ] Wire modal results and inline controls to the service. Disable categorisation without a serial number, allow uncategorisation, restrict upload/action/delegate to current assignee or Registry, and use returned detail responses as page state.
- [ ] For mark-actioned with a file, wait for the upload response before calling `action`; update upload percentage from `HttpEventType.UploadProgress`.
- [ ] Re-run the detail and service/modal specs to green, update memory, inspect the scoped diff, and commit as `feat: add workflow detail actions`.

### Task 6: Local verification and visual evidence

**Files:**
- Create: `docs/assets/pr-workflow-detail/*.png`
- Modify: `docs/nsdcc-handoff/implementation-notes.md`

- [ ] Run focused Jest specs, then `pnpm run lint`; distinguish pre-existing repo failures from changed-file failures.
- [ ] Run frontend formatting/check commands on every changed frontend file and inspect `git diff --check` plus the complete branch diff.
- [ ] Build exactly with `git -c core.autocrlf=false archive workflow-detail | docker build -t edms-local:stack -` and start the handoff compose stack.
- [ ] Seed/repair demo data only if required, then verify the detail page as `jmwangi`, `registry_ann`, and an unrelated user.
- [ ] Capture review-ready 1440x900 evidence for the overdue assignee view, Registry controls, open action dialog, history timeline, and a document-without-workflow 404 state under `docs/assets/pr-workflow-detail/`.
- [ ] Remove temporary auto-login configuration, verify the stack is restored, update memory, inspect evidence, and commit as `docs: add workflow detail evidence`.

### Task 7: Delivery and review closure

**Files:**
- Modify only files required by review feedback and the implementation notes when code changes.

- [ ] Push `workflow-detail` and open one PR against `workflow-inbox-page`; explain that `main` lacked `docs/nsdcc-handoff/` and the integrated frontend stack, link committed evidence, and do not merge.
- [ ] Monitor CI. Ignore only the documented pre-existing `prek`, `test_index`, and `test_api_schema` failures; fix regressions caused by this branch.
- [ ] Read every Copilot thread, fix or rebut with evidence, reply, resolve, and re-run affected verification after changes.
- [ ] Confirm the PR base, branch, commits, checks, evidence links, unresolved threads, and merge state before reporting.
