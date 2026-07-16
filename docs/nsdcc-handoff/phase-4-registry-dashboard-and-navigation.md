# Phase 4 PRD — Registry Dashboard, Registry Route, Sidebar Navigation

**GitHub issues:** #44 (dashboard), completes #42 (routes), sidebar half of #50.
**Branch:** `registry-dashboard` (this branch). **PR base:** `workflow-inbox-page`.
**Estimated size:** 1–2 days.

## Goal

Registry staff get a bird's-eye dashboard of ALL workflows with filtering, and the
workflow pages become discoverable from the sidebar. After this phase, issue #42 can be
closed (all three planned routes exist: inbox, registry, and the `workflow/document/:id`
redirect placeholder).

## Part A — `RegistryDashboardComponent`

New files: `src-ui/src/app/components/workflow/registry-dashboard/registry-dashboard.component.{ts,html,scss}`.
Mirror the structure/conventions of `workflow-inbox` (standalone, `PageHeaderComponent`
title "Registry Dashboard", `LoadingComponentWithPermissions`, `ToastService`,
`CustomDatePipe`, `$localize`, `@for` with `track item.id`).

Data: `NsdccWorkflowService.getRegistry(filters?: RegistryFilters)` → plain array of
`NsdccDocumentWorkflowListItem`. Backend sorts by `-created_at`; keep that order.

### Filter tabs

Bootstrap `nav nav-pills` above the table. Tabs and their `getRegistry` arguments:

| Tab             | Filter                       |
| --------------- | ---------------------------- |
| All             | none                         |
| Received        | `{status: 'received'}`       |
| Pending Action  | `{status: 'pending_action'}` |
| Actioned        | `{status: 'actioned'}`       |
| Overdue         | `{is_overdue: true}`         |
| Not Categorised | `{categorised: false}`       |

State: `activeFilter` field; switching tabs refetches (show the loading state while
fetching, keep it simple — no client-side caching). Each tab shows its label via
`$localize`. The active tab uses the `active` class.

### Table

`<table class="table table-hover align-middle">`, full width. Columns:

1. Document Title (link)
2. Document Type (`document_type`, em-dash when null)
3. Uploaded By (`uploaded_by` — display `first_name last_name`, falling back to
   `username`; copy the inbox component's user-display helper)
4. Deadline (`CustomDatePipe`; em-dash when null)
5. Status (badge — same map as inbox: received=`bg-secondary`,
   pending_action=`bg-primary`, reassigned=`bg-warning text-dark`, actioned=`bg-success`,
   overdue=`bg-danger`; label from `status_display`)
6. Categorised (`✓`-style green check or amber "Not categorised" indicator — see below)
7. Assigned To (user display, em-dash when unassigned)
8. Created (`created_at` via `CustomDatePipe`)

Row treatments:

- Overdue rows (`is_overdue`): `border-start border-danger` on the row's first cell,
  with a 4px left border via a component class — red left border, NOT the full red
  background used in the inbox (denser table, subtler cue). Do not use Bootstrap's
  `border-4`, which widens all four cell borders.
- Uncategorised rows: amber indicator in the Categorised column — a
  `bg-warning text-dark` badge reading "No" or an amber dot + text. Categorised rows get
  a muted green check (`text-success`).
- Whole row clickable → `/workflow/document/{{item.document_id}}` (redirect exists),
  same pattern as inbox (`routerLink` on title + row click handler + `cursor: pointer`).

Empty state per filter: centered message like "No workflows match this filter" (inbox
has the pattern). Error → toast + non-broken empty layout. Loading spinner while fetching.

## Part B — Route (closes #42)

In `src-ui/src/app/app-routing.module.ts`, after the `workflow/document/:id` redirect:

```ts
{
  path: 'workflow/registry',
  component: RegistryDashboardComponent,
  canActivate: [WorkflowRoleGuard],
  data: {
    componentName: 'RegistryDashboardComponent',
    requiredGroups: ['Registry'],
  },
},
```

`WorkflowRoleGuard` is already registered in `main.ts` providers. Verify manually that a
GeneralStaff user gets the toast + `/dashboard` redirect (the backend also 403s the API
for non-Registry users — the component's error toast is the fallback if someone slips
through).

After this lands, comment on issue #42 that all routes exist and close it via the PR
description (`Closes #42`, alongside `Closes #44`).

## Part C — Sidebar navigation (sidebar half of #50)

Files: `src-ui/src/app/components/app-frame/app-frame.component.html` + `.ts`.

1. **"Workflow Inbox" link** in the App-links section directly after "Documents".
   Follow the existing nav-item pattern exactly (routerLink `/workflow/inbox`,
   `routerLinkActive="active"`, `i-bs` icon `inbox` — add `inbox` to the icons object in
   `src-ui/src/main.ts` if absent — slim-sidebar `ngbPopover` support like its siblings).
2. **Inbox badge**: `<span class="badge bg-danger ms-2 d-inline">{{count}}</span>`
   (copy the Tasks badge pattern). Count = length of `getInbox()` response. Fetch on
   init and refresh with `interval(60000)` + on router `NavigationEnd` events; both
   `takeUntil`-guarded. Hide the badge entirely when count is 0. Failures are silent
   (no toast from a background poll — just keep the last value).
3. **"Registry Dashboard" link** in the Manage section, routerLink `/workflow/registry`,
   visible only when the current user is a Registry member or superuser. Implement an
   `isRegistryUser()` helper in the component using `settingsService.currentUser`
   (`is_superuser`, `group_names`) and the `nsdcc_groups` mapping via
   `settingsService.get(SETTINGS_KEYS.NSDCC_GROUPS)` — same resolution logic as
   `WorkflowRoleGuard` (default name 'Registry' → effective name → membership test).

## Tests (Jest)

- `registry-dashboard.component.spec.ts`: renders rows from mocked service; each tab
  triggers `getRegistry` with the right filter argument; overdue row gets the danger
  border class; uncategorised indicator logic; row link URLs; empty state; error toast.
- `app-frame.component.spec.ts` exists — EXTEND it (don't rewrite): badge renders with
  count, hidden at 0; registry link visible for registry user/superuser, hidden for
  staff. Mock `NsdccWorkflowService.getInbox`.
- Guard behavior is already covered by `workflow-role.guard.spec.ts`; don't duplicate.

## Evidence checklist for the PR

Live screenshots (see `README.md` §5 for the recipe), committed under
`docs/assets/pr-registry-dashboard/`:

1. Dashboard as `registry_ann` — All tab (5 seeded workflows, overdue border visible,
   categorised indicators mixed).
2. A filtered tab (e.g. Not Categorised) showing the subset.
3. Sidebar showing the Workflow Inbox link + badge count as `jmwangi` (badge "3"), and
   the Registry Dashboard link visible as `registry_ann` but absent as `jmwangi`
   (two screenshots or a side-by-side).
4. The guard redirect: navigate to `/workflow/registry` as `jmwangi` → dashboard + toast.

## Out of scope

Upload hook and initiate modal (phase 6). Any backend change. The `workflow/document/:id`
redirect stays a redirect until phase 5.
