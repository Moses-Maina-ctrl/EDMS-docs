# Phase 6 PRD — Workflow Initiate Modal + Upload Hook

**GitHub issues:** #46 (modal) + the upload-hook half of #50.
**Branch:** `initiate-modal` off the phase-5 branch. **PR base:** the phase-5 branch.
**Estimated size:** 1–2 days.

## Goal

Close the loop: when the PA uploads a scanned document, they are prompted to create the
workflow record immediately (confidentiality, deadline, instruction, optional assignee),
and any document without a workflow offers PA users an "Initiate Workflow" entry point.

## Part A — `WorkflowInitiateComponent` (modal)

New files: `src-ui/src/app/components/workflow/workflow-initiate/workflow-initiate.component.{ts,html}`.
Opened via `NgbModal.open(WorkflowInitiateComponent, { size: 'lg' })`; use
`NgbActiveModal` for close/dismiss. Inputs (set on `componentInstance`): `documentId:
number`, `filename: string` (shown in the modal header for context).

Reactive form (`FormGroup`):
| Field | Control | Validation |
|---|---|---|
| Confidentiality | select of the 4 enum values (labels via `$localize`) | required |
| Deadline | `NgbInputDatepicker` | required; format to `YYYY-MM-DD` for the API |
| Instruction | textarea | optional |
| Assign to | `<ng-select>` user picker (same pattern as phase 5 modals) | optional |

Behavior:
- Submit disabled until valid; on submit call
  `NsdccWorkflowService.initiate(documentId, data)`.
- Success: close modal, toast "Workflow created", navigate to
  `/workflow/document/{documentId}`.
- 409 (workflow already exists): toast the message, close the modal.
- Other errors: toast, keep the modal open.
- Cancel / Escape / backdrop click dismisses without side effects (a document without a
  workflow is a valid state — Registry can still see it? NO: note, unworkflowed
  documents are invisible to the NSDCC endpoints; that's accepted product behavior for
  now, see backlog item about Registry visibility of unworkflowed uploads).

## Part B — Upload hook (`AppComponent`)

File: `src-ui/src/app/app.component.ts` — inside the existing
`onDocumentConsumptionFinished()` subscription (~lines 76–107), AFTER the existing toast
logic (the toast stays):
- If the current user is PA or superuser (role helper per the `WorkflowRoleGuard`
  resolution pattern — 'PA' default name through the `nsdcc_groups` mapping), open the
  modal with the finished document's id + filename from the status payload.
- Non-PA users: unchanged behavior.
- Guard against modal spam: if multiple consumptions finish in a burst, queue or only
  open for the first and toast the rest (implementer's judgment — document the choice
  in the PR).

## Part C — "Initiate Workflow" button on document detail (AC 10 of #50)

In the workflow-detail 404 panel from phase 5 (and/or the standard document detail page
if cleaner — prefer the workflow-detail 404 panel to avoid touching the 2000-line
`document-detail.component.ts`): show an "Initiate Workflow" button for PA/superuser
users that opens the same modal. On success, reload the detail view.

## Tests (Jest)

- Modal spec: form validation states; submit calls `initiate` with the exact payload
  (date serialization!); success closes + navigates; 409 path; dismiss does not call
  the service.
- AppComponent spec exists — EXTEND: consumption-finished event opens modal for a PA
  user, not for a staff user, toast still fired in both cases.

## Evidence checklist

Screenshots: modal open with the filename in the header (as `pa_office` after a real
upload against the local stack — upload any small PDF through the UI), validation state,
the created workflow's detail page, and the sequence proving non-PA users see only the
toast. To demo a real consumption locally the container must be able to OCR the file —
the stock image includes everything needed; upload via the Documents page.

## After this phase

Close #46 and #50 (`Closes #46, closes #50` in the PR). Update the "What Remains"
section of `docs/nsdcc-workflow.md` — after phase 6 the only remaining items are the
DevOps init task and the backlog items.
