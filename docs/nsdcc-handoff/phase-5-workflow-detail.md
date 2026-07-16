# Phase 5 PRD — Workflow Detail Page

**GitHub issue:** #45 — ⚠️ the GitHub issue BODY is a copy-paste duplicate of #44 and is
wrong; THIS document (derived from `docs/nsdcc-workflow-issues.md` Issue 6) is
authoritative. Consider fixing the issue body from here when you start.
**Branch:** `workflow-detail` off the phase-4 branch. **PR base:** the phase-4 branch.
**Estimated size:** 3+ days — the largest phase. Split commits by section.

## Goal

The heart of the feature: a two-column page at `/workflow/document/:id` showing the
document (PDF viewer) beside its full workflow state, with role- and status-conditional
actions (assign, delegate, action, serialise, categorise, summary), attachments, and
the action-history timeline.

## Route change

Replace the redirect in `app-routing.module.ts`:

```ts
// before (placeholder):  { path: 'workflow/document/:id', redirectTo: 'documents/:id' },
{
  path: 'workflow/document/:id',
  component: WorkflowDetailComponent,
  data: { componentName: 'WorkflowDetailComponent' },
},
```

No guard — the API filters access (GeneralStaff only see workflows they're involved in;
the component must handle the 403).

## Component

New files under `src-ui/src/app/components/workflow/workflow-detail/`:
`workflow-detail.component.{ts,html,scss}` plus (recommended) sub-components for modals:
`action-modal/`, `delegate-modal/`, `assign-modal/` — keep each file small and testable.

Data: `NsdccWorkflowService.getDetail(documentId)` → `NsdccDocumentWorkflow` (full
nested shape: `actions[]`, `attachments[]`). `documentId` from `ActivatedRoute` params.
Re-fetch after every successful mutation (each mutating endpoint returns the updated
detail — you may use the response body directly instead of re-fetching).

### Layout

Bootstrap grid: `col-md-7` PDF viewer, `col-md-5` state panel.
PDF: `<pngx-pdf-viewer>` (`src/app/components/common/pdf-viewer/`), `src` from
`DocumentService.getPreviewUrl(workflow.document_id)`. Seeded demo documents have no
file — the viewer shows a loading/error pane; that's fine locally, note it in evidence.

### State panel sections (top to bottom; use `@if` blocks)

1. **Header**: document title (link to `/documents/:id` for the full document editor),
   status badge (same 5-status map as inbox/dashboard), confidentiality badge
   (`confidentiality_display`, `bg-secondary` is fine for all levels or vary if trivial).
2. **Deadline**: `CustomDatePipe`; when `is_overdue` (or deadline past), render in red
   with an "OVERDUE" label.
3. **Assigned to**: current assignee (user display helper). PA/Registry users see a
   "Change assignee" button → assign modal (user picker + optional instruction/deadline
   fields → `assign()`).
4. **Instruction**: full text. (The backend allows PA/Registry to update instruction
   via `assign` — expose editing only inside the assign modal; no standalone edit.)
5. **Serial number**: value or "Not set". Registry-only inline edit (small input +
   save) → `serialise({serial_number})`.
6. **Summary**: value or empty. Registry-only edit. ⚠️ BACKEND GAP: no endpoint writes
   `summary` today. This phase includes the minimal backend addition — see below.
7. **Categorised**: toggle/checkbox, Registry-only. Client-side pre-validation matching
   the backend: enable "mark categorised" only when `serial_number` is set AND the
   document has a type (`getDetail` doesn't return document_type — simplest: attempt and
   surface the backend's 400 error list as toasts; client-side check on `serial_number`
   only). Un-categorising is always allowed.
8. **Action buttons** (visible to the CURRENT ASSIGNEE while status is `pending_action`
   or `reassigned`; Registry may also act per the backend permission):
   - "Mark as Actioned" → modal: required comment textarea, optional file attachment
     (if a file is chosen, call `uploadAttachment` first, then `action({comment})`),
     submit disabled until comment non-empty.
   - "Delegate" → modal: required user picker, optional comment → `delegate()`.
9. **Attachments**: list `filename` (as `download_url` link), uploader, `uploaded_at`,
   `note`. Upload button (assignee/Registry): file input + optional note →
   `uploadAttachment(documentId, formData)` — the service returns
   `Observable<HttpEvent<...>>` with `reportProgress`; show a simple progress bar
   (`HttpEventType.UploadProgress` → percentage).
10. **History timeline**: chronological list of `actions[]` — human-readable label per
    `action_type` (use `action_type_display` from the API; it's already localised
    server-side), performer display name, `timestamp` (`CustomDatePipe`), `comment` when
    present, and for assigned/delegated entries "from X to Y" using
    `assigned_from`/`assigned_to`.

### Role helpers

Create one small utility (or component methods) reusing the `WorkflowRoleGuard`
resolution pattern: `isPA()`, `isRegistry()`, `isCurrentAssignee(workflow)`
(compare `workflow.assigned_to?.id` with `settingsService.currentUser.id`), each
OR'd with `is_superuser` where the backend does the same.

### User picker (assign/delegate modals)

`<ng-select>` fed by `UserService` (see how existing components use it — e.g.
permissions-related forms) with client-side search across the loaded user list.
Display `first_name last_name (username)`.

### Error/edge states

- 404 from `getDetail` (no workflow for this document): render a friendly "No workflow
  exists for this document" panel with a link to `/documents/:id`. (PA users will get an
  "Initiate" affordance here in phase 6 — leave a placeholder comment.)
- 403: toast "You don't have permission to view this workflow" + redirect `/dashboard`.
- All mutation errors: toast the backend's `error` message (the API returns
  `{"error": "..."}`, or a list for categorise).

## Backend addition (small, in this PR): summary endpoint

`docs/nsdcc-workflow.md` says Registry writes a Summary, and the model has the field,
but no endpoint sets it. Add, mirroring `SerialiseWorkflowView` exactly:

- `PATCH /api/nsdcc-workflow/documents/{id}/summarise/` — permission `IsRegistryOrAdmin`,
  body `{"summary": "..."}` (required, may be blank? No — require non-blank like
  serialise), sets `workflow.summary`, logs a `DocumentWorkflowAction` with the existing
  `COMMENT_ADDED` action type (comment = "Summary updated") to avoid a model migration,
  returns the detail serializer.
- Wire in `urls.py` (`nsdcc-workflow-summarise`), add `summarise(documentId, data)` to
  `NsdccWorkflowService` (+ interface `SummariseWorkflowRequest {summary: string}`), and
  backend tests in `src/nsdcc_workflows/tests/test_api.py` (permission: staff 403,
  registry 200; value persisted; action logged) plus a service spec test.
- Update the endpoint table in `docs/nsdcc-workflow.md`.

## Tests (Jest)

Component spec(s) with mocked service covering: section rendering from a full workflow
fixture; role-conditional visibility (assignee vs registry vs PA vs unrelated staff);
status-conditional buttons (actioned workflow shows no action/delegate buttons);
categorise button disabled without serial number; action modal requires comment;
delegate modal requires user; attachment upload progress event handling; 404 and 403
paths; timeline renders assigned/delegated "from → to" lines. Sub-component modals get
their own small specs.

## Evidence checklist

Screenshots as three different users (recipe in README §5): full detail page as the
assignee (`jmwangi`, overdue workflow — red deadline), as `registry_ann` (serial/summary/
categorise controls visible), the action modal open, the history timeline, and the 404
"no workflow" state (any document without a workflow — seed doc #4 'Vendor invoice
batch #88' has one, use a fresh upload or admin-created document instead).

## Out of scope

Initiate modal & upload hook (phase 6). Registry review/close/rework lifecycle (not in
the backend — see backlog). Editing instruction outside the assign modal.
