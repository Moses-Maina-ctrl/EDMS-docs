# IDMS Engineering Memory

## NSDCC workflow frontend

### Workflow detail implementation setup

`workflow-detail` is based on `origin/workflow-inbox-page` at merge commit `c8c1cf4`,
not `main`. At implementation start, `origin/main` ended at the workflow API merge and
did not contain `docs/nsdcc-handoff/`; the fallback integration branch already included
the role guard, inbox, Registry dashboard, navigation work, and the Registry dashboard
review fixes. The PR must therefore target `workflow-inbox-page` and explain this base.

The authoritative scope is `docs/nsdcc-handoff/phase-5-workflow-detail.md`. The page
replaces the `/workflow/document/:id` redirect, keeps access enforcement in the API,
and adds only the specified `summarise/` backend write path. Initiation, Registry
review/close, lifecycle terminology changes, unworkflowed-document discovery, and
other backlog items remain out of scope.

The implementation plan is recorded in
`docs/superpowers/plans/2026-07-15-workflow-detail.md`. Backend tests are written but
must run in CI rather than natively on Windows. Live verification must build from
`git archive`, use the handoff Docker stack, and commit the role-based screenshots
under `docs/assets/pr-workflow-detail/`.

The summary write path is `PATCH /api/nsdcc-workflow/documents/{document_id}/summarise/`.
It is Registry/admin-only, rejects blank input, trims and persists the summary, then
records the update with the existing `comment_added` action type and the comment
`Summary updated`. This deliberately avoids adding a model choice or migration.
The Angular contract is `SummariseWorkflowRequest { summary: string }`, exposed through
`NsdccWorkflowService.summarise(documentId, data)` and returning the updated full
workflow detail like the existing serialise and categorise methods.

Workflow assignment, delegation, and action confirmation use focused standalone
ng-bootstrap modals under `workflow-detail/`. Assign and delegate load active users
once through `UserService.listAll()` and map them to searchable `Full Name (username)`
options; validation and payload construction remain inside each modal. The action
modal returns a trimmed required comment plus an optional file, while the detail page
will own the upload-before-action sequence.

`/workflow/document/:id` now renders `WorkflowDetailComponent` without a route guard;
the detail API remains the access boundary. The page uses a responsive 7/5 Bootstrap
split for the shared PDF viewer and state panel, resolves deployment-specific PA and
Registry group names through `SETTINGS_KEYS.NSDCC_GROUPS`, and treats superusers as
both roles. A 404 stays on-page with a document-editor link, while a 403 shows the
workflow permission toast and returns the user to `/dashboard`. Workflow history is
sorted oldest-first before rendering assignment and delegation transitions.

The detail component consumes updated workflow bodies from assign, delegate, action,
serialise, summarise, and categorise mutations rather than issuing redundant detail
requests. Categorisation stays disabled until the serial number is persisted (typing
an unsaved value is insufficient); uncategorising remains available. The checkbox is
rendered only for Registry/admin users; other viewers receive a read-only Yes/No value
rather than a misleading disabled control. Standalone attachment uploads report
`HttpEventType.UploadProgress`, append the returned
attachment, and accept an optional note. Mark-as-actioned uploads its optional file
first and calls the action endpoint only after the upload response. Backend `error`
lists are emitted as one toast per message.

Local frontend verification uses the locked `src-ui` dependencies. Because the root
Prettier config resolves plugins relative to the repository root while the plugin is
installed under `src-ui/node_modules`, set `NODE_PATH` to that directory for targeted
Prettier runs. After formatting, the workflow detail/modal/service Jest selection is
38 tests across 5 suites, and `pnpm run lint` completes with all files passing.
The changed backend view, URL, and API-test files also pass scoped `ruff check` and
`ruff format --check`; Ruff reorganised the workflow URL imports into the repository's
single-import style.

The production image was built from `git archive workflow-detail` as required and run
against the seeded Docker stack. Browser verification covered General Staff assignee,
Registry, PA, and unrelated-staff sessions: conditional controls matched each role,
the Registry summary mutation persisted and added its history entry, the action modal
validated its required comment, the delegated history rendered oldest-first, a real
document without a workflow showed the in-page 404 state, and an unrelated user was
redirected with the 403 permission toast. The seeded documents have no source PDF, so
the otherwise expected blank preview also logs the documented local PDF worker/file
error; this is test-fixture behavior rather than a workflow-detail regression.

The committed visual evidence is under `docs/assets/pr-workflow-detail/`:
`assignee-overdue.png`, `registry-controls.png`, `action-modal.png`,
`history-timeline.png`, and `no-workflow.png`.

Review follow-up tightened two state boundaries. Assignee-only capabilities now require
both the workflow assignee ID and current-user ID to be present and equal, so an
unassigned workflow cannot treat two missing IDs as a match. Deadline styling also
uses only the API's `is_overdue` flag or explicit `overdue` status, keeping timezone
and end-of-day semantics centralized in the backend rather than reinterpreting the
date in the browser.

The repository's pytest configuration previously omitted `src/nsdcc_workflows/tests/`
from `testpaths`, even though the handoff defines the normal CI backend job as the
source of truth for that package. The directory is now part of standard pytest
discovery so the workflow API suite, including the summary endpoint tests, runs in CI
without a special-case workflow command.

### Phase 4: Registry Dashboard and navigation

`registry-dashboard` is stacked on `workflow-inbox-page` and implements GitHub issues
#44 and #42, plus the sidebar-navigation portion of #50. The frontend-only change
adds `RegistryDashboardComponent`, which calls `NsdccWorkflowService.getRegistry()`
without reordering its backend-sorted response. Its filter tabs issue a fresh request
for All, Received, Pending Action, Actioned, Overdue, and Not Categorised; rows link
through the temporary `/workflow/document/:id` route until the Phase 5 detail page
replaces that redirect.

Overdue rows use Bootstrap's danger left border on the document-title cell only. Do
not put those border classes on the `<tr>`: Bootstrap then draws a full red outline,
which is noisier than the specified dense-table cue. The local
`overdue-title-cell` class expands only the left border to 4px; do not use Bootstrap's
`border-4`, which widens every side of the cell.

The `workflow/registry` route is protected with `WorkflowRoleGuard` for the Registry
role. `AppFrameComponent` now includes a Workflow Inbox sidebar link with a silently
refreshed count (initial load, navigation events, and one-minute interval), and only
shows Registry Dashboard to superusers or users whose group matches the configured
`nsdcc_groups.registry` name, falling back to `Registry`.

Focused Jest coverage lives alongside the new dashboard component and extends the
existing app-frame spec. Do not add workflow lifecycle work here: Registry review/
close, status terminology, and unworkflowed documents remain explicitly out of scope.

The repository-wide `prek` check currently changes unrelated tracked files before it
reaches this work. Keep the dashboard scope tight: the only Phase 4 formatter update
is the organized import block in `app-frame.component.ts`.

Inbox refresh failures deliberately retain the last successful badge count and do not
surface a toast or console error; this matches the sidebar's background-refresh role.

## Workflow UI pass — 2026-07-16

A local browser QA pass of PRs #47–#54 and issues #41–#46/#50 is recorded in
`docs/qa/workflow-ui-pass-2026-07-16/report.md`, with page/modal screenshots
and two repro videos. It verified the new workflow routes, all Registry
filters, the non-Registry guard redirect, manual and upload-triggered
initiation, and responsive layouts. The actionable findings are: submitting
an empty Change assignee form mutates workflow status (high), DOCX upload is
accepted by the picker then rejected by the consumer (high), the Registry
table hides operational columns on mobile without a scroll cue (medium), and
the no-group dashboard emits an unhandled saved-views 403 (low). The report
also records intentional local fixture mutations made while reproducing the
issues; reset the dev seed data before treating its states as pristine.
