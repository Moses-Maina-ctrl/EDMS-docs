# NSDCC Workflow — Remaining GitHub Issues

The backend is fully implemented and deployed. The following issues cover the remaining frontend (Angular) and DevOps work.

---

## Issue 1: [Frontend] Create TypeScript Interfaces and NsdccWorkflowService

**Title:** [Frontend] Create TypeScript interfaces and NsdccWorkflowService for NSDCC workflow API

**Description**
Create the Angular service and TypeScript interfaces for all communication with the NSDCC workflow API. The backend is fully implemented at `/api/nsdcc-workflow/` with 12 endpoints. This service is the data layer that all workflow components will depend on.

**Background Context**
The NSDCC physical document workflow tracks paper documents through receipt, CEO instruction, staff assignment, actioning, and registry filing. The backend API is live and tested. The frontend needs a dedicated service to call every endpoint. This service must be separate from the existing `WorkflowService` (at `src-ui/src/app/services/rest/workflow.service.ts`) which manages Paperless's built-in workflow automation engine.

**Technical Context**
- New file: `src-ui/src/app/data/nsdcc-workflow.ts` — TypeScript interfaces
- New file: `src-ui/src/app/services/rest/nsdcc-workflow.service.ts` — service
- Existing service patterns: `src-ui/src/app/services/rest/abstract-paperless-service.ts` — generic base with `HttpClient`, `environment.apiBaseUrl`
- Existing `WorkflowService` at `src-ui/src/app/services/rest/workflow.service.ts` — DO NOT modify this file
- Auth is cookie-based (session cookies). CSRF and API version headers are attached by interceptors in `src-ui/src/main.ts:401-408`
- `environment.apiBaseUrl` is the base URL prefix
- The app uses standalone components with `inject()` for DI. Services use `@Injectable({ providedIn: 'root' })`
- Backend API docs: `docs/nsdcc-workflow.md`

**Acceptance Criteria**
1. TypeScript interfaces defined in `src-ui/src/app/data/nsdcc-workflow.ts`: `NsdccDocumentWorkflow`, `NsdccDocumentWorkflowAction`, `NsdccDocumentWorkflowAttachment`, `WorkflowUser`
2. `NsdccWorkflowService` created with `@Injectable({ providedIn: 'root' })`
3. Service methods: `initiate(documentId, data)`, `getDetail(documentId)`, `assign(documentId, data)`, `delegate(documentId, data)`, `action(documentId, data)`, `serialise(documentId, data)`, `categorise(documentId, data)`, `uploadAttachment(documentId, formData)`, `getAttachments(documentId)`, `getHistory(documentId)`, `getInbox()`, `getRegistry(filters?)`
4. All methods return typed `Observable`s
5. Base URL is `environment.apiBaseUrl + 'nsdcc-workflow/'`
6. Multipart upload uses `FormData` with `reportProgress: true` and `observe: 'events'`

**Implementation Notes**
- Do NOT extend `AbstractPaperlessService` — the NSDCC API shape (action-based endpoints) doesn't match the standard CRUD pattern
- Use `inject(HttpClient)` in the constructor
- The `getRegistry()` method should accept optional query params: `status`, `categorised`, `is_overdue`
- Read the backend serializers in `src/nsdcc_workflows/serializers.py` to understand the exact response shape

**Dependencies:** None (backend is deployed and running)
**Estimated Complexity:** Medium (one to two days)

---

## Issue 2: [Frontend] Create Workflow Role Guard

**Title:** [Frontend] Create WorkflowRoleGuard for group-based route access control

**Description**
Create a custom Angular route guard that restricts access to routes based on the user's Django auth group membership (PA, Registry, GeneralStaff). The Registry Dashboard must only be accessible to Registry group members.

**Background Context**
The NSDCC workflow uses three organisational roles implemented as Django auth Groups. The existing `PermissionsGuard` checks Django model permissions (add/view/change/delete), which doesn't map to our group-based roles. We need a separate guard that checks group membership.

**Technical Context**
- New file: `src-ui/src/app/guards/workflow-role.guard.ts`
- Existing guard pattern: `src-ui/src/app/guards/permissions.guard.ts` — implements `canActivate(route, state)`, redirects to `/dashboard` on failure
- The user object from settings includes `groups` (array of group IDs) and `is_superuser` boolean
- Route data configuration: `data: { requiredGroups: ['Registry'] }`
- The guard needs to resolve group IDs to group names. Options: (A) add `nsdcc_groups` to the UI settings backend response, (B) call a new API endpoint to get user's groups, (C) hardcode known group IDs after fetching them once at app init
- Register the guard in `src-ui/src/main.ts` providers

**Acceptance Criteria**
1. Given a route with `data: { requiredGroups: ['Registry'] }`, when a Registry group member navigates to it, access is granted
2. Given a superuser navigates to the route, access is granted regardless of group membership
3. Given a non-Registry, non-superuser navigates to the route, they are redirected to `/dashboard` with a toast message
4. The guard supports multiple groups in `requiredGroups` (any match grants access)

**Implementation Notes**
- The cleanest approach is to add a small backend addition: expose the user's group names in the UI settings response (`src/documents/views.py` `UiSettingsView`). Add `nsdcc_groups: [list of group names the user belongs to]` to the response dict. This is a 5-line backend change.
- Alternatively, fetch groups once at app init via `GET /api/groups/` and cache them.
- Use the same redirect pattern as `PermissionsGuard`: `this.router.parseUrl('/dashboard')`

**Dependencies:** Issue 1 (NsdccWorkflowService)
**Estimated Complexity:** Medium (one to two days)

---

## Issue 3: [Frontend] Add Workflow Routes to App Routing

**Title:** [Frontend] Add workflow/inbox, workflow/registry, and workflow/document/:id routes

**Description**
Add three new routes to the Angular routing configuration for the NSDCC workflow pages. All routes must be children of the `AppFrameComponent` shell (same as all other pages).

**Background Context**
The workflow system needs three pages: an inbox for all users, a registry dashboard for the Registry team, and a detail page for individual workflows.

**Technical Context**
- File: `src-ui/src/app/app-routing.module.ts`
- Existing routes are children of the `AppFrameComponent` layout route
- Guards: `PermissionsGuard` (existing), `WorkflowRoleGuard` (from Issue 2)
- Components are standalone and imported directly

**Acceptance Criteria**
1. Route `workflow/inbox` maps to `WorkflowInboxComponent`, accessible to all authenticated users
2. Route `workflow/registry` maps to `RegistryDashboardComponent`, guarded by `WorkflowRoleGuard` with `requiredGroups: ['Registry']`
3. Route `workflow/document/:id` maps to `WorkflowDetailComponent`, accessible to all authenticated users (access filtering happens in the component via the API)
4. All three routes are children of the `AppFrameComponent` shell route
5. Each route has `data.componentName` set

**Implementation Notes**
- Add routes inside the existing children array of the `AppFrameComponent` route
- Import the new components at the top of the file
- The `WorkflowRoleGuard` must be registered in `main.ts` providers

**Dependencies:** Issues 2, 4, 5, 6 (guard and components must exist)
**Estimated Complexity:** Small (half a day)

---

## Issue 4: [Frontend] Build Workflow Inbox Component

**Title:** [Frontend] Build WorkflowInboxComponent showing user's pending documents

**Description**
Create the Workflow Inbox page that shows all documents currently assigned to the logged-in user and awaiting action. This is the primary landing page for General Staff users.

**Background Context**
Staff members need to see their pending work — documents assigned or delegated to them. Overdue items must be immediately visible at the top with red highlighting.

**Technical Context**
- New files: `src-ui/src/app/components/workflow/workflow-inbox/workflow-inbox.component.ts`, `.html`, `.scss`
- Service: `NsdccWorkflowService.getInbox()` (from Issue 1)
- Existing list patterns: `src-ui/src/app/components/document-list/document-list.component.ts`
- Component must be standalone, use `inject()` for DI
- Table styling: Bootstrap 5

**Acceptance Criteria**
1. Table with columns: Document Title, Document Type, Assigned By, Instruction Preview (first 80 chars), Deadline, Status
2. Overdue items sorted to top and highlighted with red background/border
3. Each row clickable, navigates to `/workflow/document/{documentId}`
4. Empty state shown with clear message when no pending items
5. Loading spinner and error toast handling
6. Status badge colours: Pending Action = blue (`bg-primary`), Reassigned = amber (`bg-warning text-dark`), Overdue = red (`bg-danger`)

**Implementation Notes**
- Use `<table class="table table-hover">` with Bootstrap styling
- Truncate instruction at 80 characters with ellipsis
- Use Angular `DatePipe` for deadline formatting
- Add `trackBy` function for `@for` loop performance

**Dependencies:** Issue 1
**Estimated Complexity:** Medium (one to two days)

---

## Issue 5: [Frontend] Build Registry Dashboard Component

**Title:** [Frontend] Build RegistryDashboardComponent with filtering and status indicators

**Description**
Create the Registry Dashboard page showing all workflow records with filtering, for the Registry team's oversight of the document lifecycle.

**Background Context**
The Registry team manages serialisation, categorisation, and physical filing. They need a bird's-eye view to identify items needing serial numbers, overdue items, and items ready for categorisation.

**Technical Context**
- New files: `src-ui/src/app/components/workflow/registry-dashboard/registry-dashboard.component.ts`, `.html`, `.scss`
- Service: `NsdccWorkflowService.getRegistry(filters)` (from Issue 1)
- Filter tabs: Bootstrap nav-pills or similar
- Table pattern: same as inbox but with more columns

**Acceptance Criteria**
1. Full-width table with columns: Document Title, Document Type, Uploaded By, Deadline, Status, Categorised, Assigned To, Created Date
2. Filter tabs: All, Received, Pending Action, Actioned, Overdue, Not Categorised
3. Each row clickable, navigates to `/workflow/document/{documentId}`
4. Overdue rows highlighted with red left border or background tint
5. Uncategorised rows shown with amber indicator
6. Only accessible to Registry group members (enforced by route guard)
7. Loading, error, and empty state handling

**Implementation Notes**
- Implement filter tabs as a state variable (`activeFilter`) passed to `getRegistry()`
- For "Not Categorised" filter, pass `categorised=false`
- Use `border-start border-4 border-danger` for overdue rows
- Use `border-start border-4 border-warning` for uncategorised rows

**Dependencies:** Issues 1, 2
**Estimated Complexity:** Medium (one to two days)

---

## Issue 6: [Frontend] Build Workflow Detail Component

**Title:** [Frontend] Build WorkflowDetailComponent with PDF viewer, state panel, and action modals

**Description**
Create the Workflow Detail page with a two-column layout: PDF viewer on the left, workflow state panel on the right. This is the most complex frontend component — it shows full workflow state, allows actions (assign, delegate, action, serialise, categorise), uploads attachments, and displays the action history timeline.

**Background Context**
Users need to see the document while working on the workflow. The right panel shows status, confidentiality, deadline, assignee, instruction, serial number, summary, categorisation state, action buttons (conditional on role and status), attachments, and the full action history.

**Technical Context**
- New files: `src-ui/src/app/components/workflow/workflow-detail/workflow-detail.component.ts`, `.html`, `.scss`
- PDF viewer: `src-ui/src/app/components/common/pdf-viewer/pdf-viewer.component.ts` — standalone, selector `pngx-pdf-viewer`. Inputs: `src` (PdfSource), `page`, `renderMode`, `selectable`, `searchQuery`, `zoom`, `zoomScale`
- PDF source URL: `DocumentService.getPreviewUrl(documentId)` returns the URL string
- Existing detail patterns: `src-ui/src/app/components/document-detail/document-detail.component.ts` (1986 lines)
- Service: `NsdccWorkflowService` for all API calls
- User picker: use `ng-select` with `UserService` for searchable user selection
- Bootstrap 5 grid: `col-md-7` / `col-md-5` for two-column layout
- Modals: use `NgbModal` from `@ng-bootstrap/ng-bootstrap`

**Acceptance Criteria**
1. Two-column layout: left = PDF viewer (`pngx-pdf-viewer`), right = workflow state panel
2. Status badge colour-coded: Received = grey, Pending Action = blue, Reassigned = amber, Actioned = green, Overdue = red
3. Confidentiality level badge displayed
4. Deadline shown in red with "OVERDUE" label if past deadline
5. Assigned to section shows current assignee name. PA/Registry users see "Change Assignee" button opening user picker
6. Instruction section shows full text. PA users see edit button
7. Serial number section shows value. Registry users see editable field
8. Summary section shows value. Registry users see editable field
9. Categorised toggle visible only to Registry users. Client-side validation matches backend (serial_number + document_type required before setting to true)
10. "Mark as Actioned" button visible only to current assignee when status is `pending_action` or `reassigned`. Opens modal with required comment field and optional file attachment
11. "Delegate" button visible only to current assignee when status is `pending_action` or `reassigned`. Opens modal with user picker and optional comment
12. Attachments section lists all attachments with filename, uploaded by, date, note, download link. Upload button visible to current assignee
13. Action history timeline shows all actions chronologically with human-readable labels, performed by name, timestamp, and comments
14. Handles loading, 404 (no workflow exists), and 403 (permission denied) states

**Implementation Notes**
- Break the right panel into logical sections using `@if` blocks
- Get PDF preview URL from `DocumentService.getPreviewUrl(workflow.document_id)`
- Human-readable action labels: map `action_type` to display strings (e.g., `uploaded` → "Document Uploaded", `delegated` → "Delegated to User")
- For the user picker, use `<ng-select>` with server-side search
- Consider creating sub-components for the modals if the template becomes too large
- Use `AsyncPipe` where possible

**Dependencies:** Issue 1
**Estimated Complexity:** Large (three or more days)

---

## Issue 7: [Frontend] Build Workflow Initiation Modal

**Title:** [Frontend] Build WorkflowInitiateComponent modal for post-upload workflow creation

**Description**
Create a modal component that opens after a successful document upload, allowing the PA to initiate a workflow for the newly uploaded document.

**Background Context**
When the PA uploads a document, they should be prompted to create a workflow record — setting confidentiality, deadline, instruction, and optionally assigning it. This modal is the primary entry point for new workflows.

**Technical Context**
- New files: `src-ui/src/app/components/workflow/workflow-initiate/workflow-initiate.component.ts`, `.html`
- Upload success handling: `src-ui/src/app/app.component.ts:79-107` — `onDocumentConsumptionFinished()` WebSocket event fires with `status` containing `documentId` and `filename`
- Modal pattern: `NgbModal` from `@ng-bootstrap/ng-bootstrap`, `NgbActiveModal` for close/dismiss
- Form: `FormGroup` with confidentiality (select, required), deadline (date picker, required), instruction (textarea, optional), assign_to (ng-select user picker, optional)
- Service: `NsdccWorkflowService.initiate(documentId, data)`
- Date picker: `NgbInputDatepicker` from ng-bootstrap

**Acceptance Criteria**
1. Modal has fields: Confidentiality Level (required select: public/internal/confidential/restricted), Deadline (required date picker), Instruction (optional textarea), Assign To (optional searchable user picker)
2. On submit, initiate API is called. On success, modal closes and user navigates to `/workflow/document/{documentId}`
3. Modal is dismissible — clicking outside, Escape, or Cancel closes without creating workflow
4. Form validation: confidentiality and deadline required. Submit disabled until valid
5. 409 error (workflow exists) shows toast and closes modal
6. Document filename shown in modal header for context

**Implementation Notes**
- Use `NgbModal.open(WorkflowInitiateComponent, { size: 'lg' })`
- The modal should only auto-open for PA/superuser users (see Issue 8 for the hook)
- User picker should call `UserService` for searchable selection

**Dependencies:** Issue 1
**Estimated Complexity:** Medium (one to two days)

---

## Issue 8: [Frontend] Hook Workflow Initiation into Upload Flow and Add Sidebar Navigation

**Title:** [Frontend] Integrate workflow initiation modal into upload flow and add sidebar navigation with inbox badge

**Description**
Two related tasks: (1) Modify `AppComponent` to open the workflow initiation modal after successful document upload for PA/superuser users. (2) Add "Workflow Inbox" and "Registry Dashboard" links to the sidebar with an inbox badge count.

**Background Context**
The upload flow is asynchronous: HTTP POST returns a task ID, backend processes the document, WebSocket fires `onDocumentConsumptionFinished` with the `documentId`. The modal must trigger at this point. Additionally, the sidebar needs workflow navigation links with a live inbox count badge.

**Technical Context**
- Upload hook file: `src-ui/src/app/app.component.ts:76-107` — the `onDocumentConsumptionFinished` subscription
- Sidebar file: `src-ui/src/app/components/app-frame/app-frame.component.html` (386 lines) and `.ts`
- Sidebar nav item pattern: `<li class="nav-item app-link"><a class="nav-link" routerLink="..." routerLinkActive="active" ...><i-bs class="me-2" name="..."></i-bs><span>...</span></a></li>`
- Badge pattern (from Tasks, line 298): `<span class="badge bg-danger ms-2 d-inline">{{count}}</span>`
- Slim sidebar popover: `ngbPopover="..." [disablePopover]="!slimSidebarEnabled"`
- Icons: `ngx-bootstrap-icons` — add `inbox` icon to `src-ui/src/main.ts` icons object if not present

**Acceptance Criteria**

*Upload Hook:*
1. After document consumption finishes, if user is PA/superuser, the workflow initiation modal opens with the new document's ID
2. For non-PA users, only the existing toast notification appears (no modal)
3. The existing toast ("Document X was added to IDMS") still appears alongside the modal
4. If the PA dismisses the modal, the document exists without a workflow (valid state)

*Sidebar:*
5. "Workflow Inbox" link appears after "Documents" in the App links section, with an inbox badge showing pending count
6. Badge count refreshes every 60 seconds and on navigation events
7. "Registry Dashboard" link appears in the Manage section, visible only to Registry group members or superusers
8. Both links work in slim sidebar mode with popover labels
9. Badge hidden when count is 0

*Document Detail Page:*
10. An "Initiate Workflow" button appears on the document detail page for documents without a workflow (PA/superuser only)

**Implementation Notes**
- In `AppComponent`, after the existing toast code (line 92-105), add: if user is PA/superuser, open the modal
- For inbox badge: inject `NsdccWorkflowService`, call `getInbox()` on init and every 60s via `interval(60000)`
- For Registry visibility: add `isRegistryUser()` method checking group membership
- For the document detail "Initiate Workflow" button: call `NsdccWorkflowService.getDetail(documentId)` — if 404, show button
- Add `inbox` icon to `src-ui/src/main.ts` icons object

**Dependencies:** Issues 3, 7
**Estimated Complexity:** Medium (one to two days)

---

## Issue 9: [DevOps] Add Management Command to Docker Container Init

**Title:** [DevOps] Add create_workflow_groups to Docker container initialization

**Description**
Ensure the `create_workflow_groups` management command runs as part of the Docker container startup so the PA, Registry, and GeneralStaff groups exist before any user tries to use the workflow feature.

**Background Context**
The workflow permission system depends on three Django auth groups. If they don't exist, all permission checks fail. The groups must be created during deployment, not manually.

**Technical Context**
- Docker init scripts: `docker/rootfs/etc/s6-overlay/s6-rc.d/` — s6-overlay service definitions
- Existing init flow: `init-migrations` → `init-superuser` → `init-system-checks`
- Management command: `python manage.py create_workflow_groups` (already implemented and tested)

**Acceptance Criteria**
1. After a fresh Docker container start, the three groups exist in the database
2. On subsequent restarts, the command runs idempotently (no errors, no duplicates)
3. The command runs after migrations have been applied

**Implementation Notes**
- Simplest approach: add `python manage.py create_workflow_groups` to the `init-superuser` or `init-custom-init` s6 service script
- Alternatively, create a new oneshot service `init-workflow-groups` depending on `init-migrations`
- The command is already idempotent (uses `get_or_create`)

**Dependencies:** None (management command already exists)
**Estimated Complexity:** Small (half a day)

---

## Dependency Graph

```
Issue 1 (NsdccWorkflowService)
├── Issue 2 (Role Guard) ──────────┐
├── Issue 4 (Inbox UI)             │
├── Issue 5 (Registry UI) ─────────┤
├── Issue 6 (Detail UI) ───────────┤
├── Issue 7 (Initiate Modal) ──────┤
│                                   │
│   Issue 2 + 4 + 5 + 6 + 7 ── Issue 3 (Routes)
│                                   │
│   Issue 3 + Issue 7 ──────── Issue 8 (Upload Hook + Sidebar)
│
Issue 9 (DevOps) — independent, no deps
```

### Parallel Work Streams

**Stream A (Service + Guard):** Issue 1 → Issue 2

**Stream B (Components):** Issue 1 → Issues 4, 5, 6, 7 (all parallel after Issue 1)

**Stream C (Integration):** Issues 3, 8 (after components are done)

**Stream D (DevOps):** Issue 9 (independent, can start immediately)

### Sprint Allocation

| Week | Stream A | Stream B | Stream C | Stream D |
|------|----------|----------|----------|----------|
| 1 | Issues 1, 2 | — | — | Issue 9 |
| 2 | — | Issues 4, 5 | — | — |
| 3 | — | Issues 6, 7 | — | — |
| 4 | — | — | Issues 3, 8 | — |
