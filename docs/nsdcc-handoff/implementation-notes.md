# IDMS Engineering Memory

## NSDCC workflow frontend

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
