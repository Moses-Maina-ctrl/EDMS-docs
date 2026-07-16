# EDMS workflow UI pass

| Field | Value |
| --- | --- |
| Date | 2026-07-16 |
| URL | http://localhost:8000 |
| Account | local `admin` seed account |
| Scope | PRs #47–#54; issues #41–#46 and #50 |

## Test plan

1. Baseline: visual hierarchy, navigation, browser errors, and responsive layout.
2. Discovery: Workflow Inbox, badge refresh/zero state, Registry Dashboard role visibility, and route behavior.
3. Workflow lists: loading, populated/empty/error states, row navigation, overdue/uncategorised treatment, and all registry filters.
4. Detail: action affordances, permission/status boundaries, history, attachment, and no-workflow/forbidden states.
5. Initiation: upload completion, required-field validation, cancellation, creation, conflict feedback, and the no-workflow recovery action.
6. Accessibility: keyboard-only modal/navigation checks, focus, labels, and responsive desktop/tablet/mobile scans.

## Change map: before → after — why

| Issue / PR | Before → after | Why |
| --- | --- | --- |
| #41 / PR #48 | Role checks only had group IDs and workflow routes had no role-aware guard → settings expose user group names and the deployment role mapping, with a guard that allows the configured role or a superuser and otherwise redirects. | Prevent Registry-only oversight screens being reached by general staff. |
| #42 / PRs #49, #51, #53 | The workflow pages had no application routes → Inbox, Registry, and document-detail pages are routed inside the normal application shell. | Make each lifecycle screen reachable through the same authenticated UI frame. |
| #43 / PR #49 | Assignees had no focused pending-work view → a Workflow Inbox presents pending/reassigned/overdue documents, states, and row navigation. | Give staff a clear action queue and surface overdue work. |
| #44 / PR #51 | Registry staff had no lifecycle overview → the Registry Dashboard provides six filters, status/categorisation cues, row navigation, and sidebar discovery. | Support operational supervision rather than forcing document-by-document inspection. |
| #45 / PR #53 | Inbox rows went to the generic document page → a workflow-aware detail screen adds preview, state, actions, serialisation, summary, categorisation, attachments, and history. | Put the workflow context and permitted next actions in one place. Note: issue #45's body is a duplicated Registry brief; the PR is the reliable source for its actual detail-page scope. |
| #46 / PR #54 | A successful PA upload ended without a workflow creation path → a validated Initiate Workflow modal is available after upload and from a no-workflow detail state. | Close the gap between document ingestion and workflow creation. |
| #50 / PRs #51 and #54 | Inbox/Registry routes were undiscoverable and uploads did not start workflows → sidebar links, an inbox badge, Registry visibility rules, and the upload initiation hook were added. | Make the workflow feature discoverable and reduce missed workflow creation. |
| PR #47 | The frontend lacked a workflow client and overdue records disappeared from inbox results → typed service contracts, serializer fields, overdue inclusion, and query safeguards were added. | Make the inbox/dashboard UI possible and ensure urgent work is not silently omitted. |
| PR #52 | The stacked #48/#49/#51 work had merged into parent branches rather than `main` → the reviewed work was consolidated into `main` without new product behavior. | Repair delivery lineage so the completed UI is actually shipped. |

## Passes observed

- Desktop sidebar discovery, empty Workflow Inbox, help text, Registry Dashboard, all six Registry filters, and row-to-detail navigation.
- Desktop workflow detail views, action/delegate/assignee modal presentation, manual initiation from a no-workflow document, and success confirmation.
- Upload of a PDF: consumption completion opened the Initiate Workflow modal automatically; cancelling it left the uploaded document available without a workflow.
- Role boundary: a temporary authenticated user outside the NSDCC groups was redirected from Registry Dashboard to Dashboard and did not see the Registry link.
- Mobile sidebar opening and workflow-detail layout; Registry data can be reached through horizontal table scrolling (see ISSUE-002 for its discoverability problem).

## Coverage limits

- The inbox badge's non-zero count and 60-second refresh could not be confirmed with a suitably assigned seed user.
- A true Registry-group login, attachment upload, assignment success, 409 initiation conflict, and every API error state remain targeted follow-ups; they were not guessed or forced.

## Local test-data effects

This was the local `dev-env` only; no repository or remote data was changed. The test created then deleted the temporary no-group user `ui_qa_nonregistry_20260716`. It also intentionally left local workflow fixtures changed while reproducing ISSUE-001: document 1 moved from Overdue to Pending Action and document 9 moved from Actioned to Pending Action. Document 6 received a workflow through the successful manual-initiation test, and `simple.pdf` was uploaded as local document 10 with initiation dismissed. Reset the local dev seed data before relying on its original fixture states.

## Findings

### ISSUE-001: Empty assignee submission changes workflow state

| Field | Value |
| --- | --- |
| Severity | High |
| Category | Functional / data integrity |
| URL | `/workflow/document/9` |
| Repro video | [issue-001-empty-assignee-submission.webm](videos/issue-001-empty-assignee-submission.webm) |

The **Change assignee** dialog presents an empty assignee picker but keeps **Assign** enabled. Submitting it closes the dialog and moves an Actioned workflow to Pending Action without showing a validation error or choosing a new assignee. The same behavior changed an Overdue workflow to Pending Action during the initial confirmation.

Expected: the client must require an assignee and the server must reject a missing assignee without changing workflow status. Proposed fix: make the picker required, disable **Assign** until a valid user is selected, surface inline validation, and retain a backend validation guard so invalid requests have no state-changing side effects.

Repro:

1. Start from the Actioned `simple` workflow. [Screenshot](screenshots/issue-001-step-1-actioned-row.png)
2. Open the workflow detail. [Screenshot](screenshots/issue-001-step-2-actioned-detail.png)
3. Click **Change assignee** and leave the picker empty. [Screenshot](screenshots/issue-001-step-3-empty-assignee-modal.png)
4. Click **Assign**. **Observed:** the status becomes Pending Action. [Screenshot](screenshots/issue-001-result-status-changed.png)

### ISSUE-002: Registry dashboard hides its most important columns on mobile

| Field | Value |
| --- | --- |
| Severity | Medium |
| Category | Responsive UX |
| URL | `/workflow/registry` at 390 × 844 |
| Repro video | N/A — visible on load |

The registry table opens with only Document Title, Type, Uploaded By, and Deadline visible. Status, categorisation, assignee, and created date are off-screen; there is no scrollbar, fade cue, or “swipe to see more” affordance. The hidden columns can be reached only after a horizontal-scroll action, which is not discoverable from the screen.

Expected: staff should immediately understand that the table contains horizontally scrollable operational fields, or receive a mobile-appropriate row layout. Proposed fix: use responsive cards below a breakpoint, or retain the table with a visible horizontal scrollbar plus a sticky first column and an explicit swipe/scroll cue.

- Initial mobile view: [Screenshot](screenshots/mobile-registry-dashboard.png)
- Status appears only after horizontal scrolling: [Screenshot](screenshots/mobile-registry-status-column-scrollintoview.png)

### ISSUE-003: Word documents are accepted by the chooser then rejected after upload

| Field | Value |
| --- | --- |
| Severity | High |
| Category | Functional / UX |
| URL | `/dashboard` |
| Repro video | [issue-003-docx-upload-rejected.webm](videos/issue-003-docx-upload-rejected.webm) |

The dashboard’s generic **Upload documents** control accepts a `.docx` selection, uploads it, then fails with a long raw MIME-type message: `application/vnd.openxmlformats-officedocument.wordprocessingml.document not supported`. This reproduces the rejected Word-document state supplied in the original screenshot.

Expected: if Word documents are a supported EDMS input, the consumer must accept and process them. If they are intentionally unsupported, the chooser must prevent selection and state the accepted formats before upload. Proposed fix: first restore/verify the DOCX consumer capability and its conversion dependencies; independently, add an upload accept list and a short actionable error such as “Word documents are not enabled here. Upload PDF, TIFF, PNG, or JPG.”

1. Open Dashboard upload. [Screenshot](screenshots/issue-003-step-1-dashboard-upload.png)
2. Select `sample.docx`.
3. **Observe:** processing fails after selection. [Screenshot](screenshots/issue-003-result-docx-unsupported.png)

### ISSUE-004: A basic authenticated user lands with an unhandled 403 console error

| Field | Value |
| --- | --- |
| Severity | Low |
| Category | Console / permissions UX |
| URL | `/dashboard` after denied `/workflow/registry` navigation |
| Repro video | N/A — visible on load |

The non-Registry guard correctly redirects an authenticated no-group user to Dashboard, but the page immediately requests `/api/saved_views/?page=1&page_size=100000` and logs an unhandled `403 Forbidden` error twice. The visible redirect works; the error is unnecessary permission noise and risks masking genuine client failures.

Proposed fix: do not request saved views until the user has view permission, or handle the expected 403 locally and expose Saved Views as unavailable rather than emitting console errors.

- Redirect destination and role-limited navigation: [Screenshot](screenshots/registry-guard-nonregistry-user.png)
