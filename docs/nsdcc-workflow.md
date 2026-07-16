# NSDCC Physical Document Workflow — Implementation Guide

## Overview

This document describes the NSDCC physical document workflow feature that has been added to IDMS. It tracks the physical lifecycle of paper documents as they move through the NSDCC organisation: from receipt by the PA (Personal Assistant), through CEO instruction and staff assignment, to actioning and final registry filing.

## What Was Added

### Django App: `nsdcc_workflows`

A new Django app at `src/nsdcc_workflows/` containing:

| File | Purpose |
|------|---------|
| `models.py` | Three models: `DocumentWorkflow`, `DocumentWorkflowAction`, `DocumentWorkflowAttachment` |
| `serializers.py` | DRF serializers for all models plus a lightweight `WorkflowUserSerializer` |
| `views.py` | 12 API endpoints covering the full workflow lifecycle |
| `urls.py` | URL routing under `/api/nsdcc-workflow/` |
| `permissions.py` | Three DRF permission classes for role-based access control |
| `notifications.py` | Three email notification functions |
| `tasks.py` | Celery periodic task for overdue document detection |
| `admin.py` | Django admin registration for all three models |
| `management/commands/create_workflow_groups.py` | Creates PA, Registry, GeneralStaff groups |

### Database Tables

Three new tables created by migration `nsdcc_workflows.0001_initial`:

- `nsdcc_workflows_documentworkflow` — main workflow record linked 1:1 to a Paperless document
- `nsdcc_workflows_documentworkflowaction` — append-only action history
- `nsdcc_workflows_documentworkflowattachment` — supplementary file attachments

### API Endpoints

All endpoints are under `/api/nsdcc-workflow/`:

| Method | URL | Permission | Purpose |
|--------|-----|-----------|---------|
| POST | `documents/{id}/initiate/` | PA or superuser | Create workflow for a document |
| GET | `documents/{id}/` | Authenticated (filtered) | Full workflow detail with nested actions/attachments |
| PATCH | `documents/{id}/assign/` | PA or Registry | Assign to a user with instruction/deadline |
| PATCH | `documents/{id}/delegate/` | Assignee or Registry | Delegate to another user |
| PATCH | `documents/{id}/action/` | Assignee or Registry | Mark as actioned with comment |
| PATCH | `documents/{id}/serialise/` | Registry | Set serial number for filing |
| PATCH | `documents/{id}/summarise/` | Registry | Set a non-blank workflow summary |
| PATCH | `documents/{id}/categorise/` | Registry | Toggle categorised (validates serial_number + document_type) |
| POST | `documents/{id}/attachments/upload/` | Assignee or Registry | Upload supplementary file |
| GET | `documents/{id}/attachments/` | Authenticated (filtered) | List attachments |
| GET | `documents/{id}/history/` | Authenticated (filtered) | Action history timeline |
| GET | `inbox/` | Authenticated | User's pending items (assigned to them) |
| GET | `registry/` | Registry | All workflows with filtering |

### Permission Model

Three Django auth groups control access:

| Group | Role | Capabilities |
|-------|------|-------------|
| **PA** | Personal Assistant | Initiate workflows, assign documents |
| **Registry** | Records Management | All PA capabilities + serialise, categorise, view all workflows, delegate on behalf of others |
| **GeneralStaff** | Regular Staff | View assigned documents, delegate, action |

Group names are configurable via environment variables to match your Entra ID role names:

| Env Var | Default | Purpose |
|---------|---------|---------|
| `PAPERLESS_NSDCC_PA_GROUP` | `PA` | Group name for PA role |
| `PAPERLESS_NSDCC_REGISTRY_GROUP` | `Registry` | Group name for Registry role |
| `PAPERLESS_NSDCC_GENERAL_STAFF_GROUP` | `GeneralStaff` | Group name for General Staff role |

Superusers bypass all permission checks.

Create groups: `python manage.py create_workflow_groups`

### Email Notifications

Three notification functions in `notifications.py`:

| Function | Trigger | Recipients |
|----------|---------|-----------|
| `notify_registry_upload` | New workflow initiated | All Registry group users |
| `notify_user_assigned` | Document assigned/delegated | The assigned user |
| `notify_registry_actioned` | Document actioned | All Registry group users |

All notifications are wrapped in try/except — email failures are logged but never cause API errors. Notifications are skipped entirely when `EMAIL_ENABLED` is `False` (SMTP not configured).

### Celery Task

`flag_overdue_documents` runs daily at 00:01 via Celery beat. It:
1. Queries workflows where `deadline < today`, status is `pending_action` or `reassigned`, and `is_overdue = False`
2. Sets `status = overdue` and `is_overdue = True`
3. Writes a `DocumentWorkflowAction` with type `overdue_flagged`

### Workflow Status Flow

```
received → pending_action → reassigned → actioned
                ↓               ↓
              overdue         overdue
```

- **received**: Document logged, not yet assigned
- **pending_action**: Assigned to a user, awaiting action
- **reassigned**: Delegated from one user to another
- **actioned**: Work completed, ready for registry filing
- **overdue**: Deadline passed without action (set automatically by Celery task)

### Access Filtering

The detail, history, and attachment list endpoints apply role-based filtering:
- **Registry and PA**: See all workflows
- **General Staff**: See only workflows where they are the current assignee OR appear in the action history (as `performed_by`, `assigned_from`, or `assigned_to` on any action record)

### Categorisation Validation

Before allowing `categorised` to be set to `true`, the API validates:
1. `serial_number` is not blank
2. The linked Paperless document has a `document_type` set

Setting `categorised` to `false` has no preconditions.

## Configuration

### Group Names (Must Match Entra ID Roles)

If your Entra ID `roles` claim uses different names than the defaults, configure:

```yaml
PAPERLESS_NSDCC_PA_GROUP: NSDCC-PA
PAPERLESS_NSDCC_REGISTRY_GROUP: NSDCC-Registry
PAPERLESS_NSDCC_GENERAL_STAFF_GROUP: NSDCC-Staff
```

Then re-run `python manage.py create_workflow_groups` to create the correctly-named groups.

### Email (Required for Notifications)

Uncomment and configure in `docker-compose.yml`:

```yaml
PAPERLESS_EMAIL_HOST: smtp.example.com
PAPERLESS_EMAIL_PORT: 587
PAPERLESS_EMAIL_HOST_USER: noreply@example.com
PAPERLESS_EMAIL_HOST_PASSWORD: changeme
PAPERLESS_EMAIL_FROM: noreply@example.com
PAPERLESS_EMAIL_USE_TLS: "true"
```

### Deployment

After deploying, run:
```bash
python manage.py migrate nsdcc_workflows
python manage.py create_workflow_groups
```

## What Remains

The following components are not yet implemented and are tracked as GitHub issues:

### Frontend (Angular)
- `NsdccWorkflowService` — TypeScript service for all API calls
- `WorkflowRoleGuard` — route guard for Registry-only pages
- `WorkflowInboxComponent` — user's pending items page
- `RegistryDashboardComponent` — Registry oversight page with filtering
- `WorkflowDetailComponent` — two-column detail view with PDF viewer
- `WorkflowInitiateComponent` — modal for initiating workflows after upload
- Sidebar navigation additions with inbox badge
- Upload flow hook to auto-open initiation modal

### DevOps
- Add `create_workflow_groups` to Docker container init scripts

## Testing the API

```bash
# Get auth token
docker-compose exec webserver python manage.py drf_create_token <username>

# Initiate workflow
curl -X POST -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"confidentiality": "internal", "deadline": "2026-07-20", "instruction": "Review and action"}' \
  http://localhost:8000/api/nsdcc-workflow/documents/<doc_id>/initiate/

# View inbox
curl -H "Authorization: Token <token>" http://localhost:8000/api/nsdcc-workflow/inbox/

# View registry
curl -H "Authorization: Token <token>" http://localhost:8000/api/nsdcc-workflow/registry/
```

## Architecture Decisions

1. **Separate app (`nsdcc_workflows`)**: Avoids naming collision with Paperless's built-in `Workflow` model and `WorkflowService`.
2. **Group-based permissions**: Simpler than Django Guardian for this use case — access is determined by organisational role, not per-object ownership.
3. **Append-only action log**: `DocumentWorkflowAction` is separate from the existing `django-auditlog` system. The auditlog tracks field-level changes on models; our action log tracks domain-specific business events.
4. **Notification independence**: Email failures never block API operations. The database write and notification are independent.
5. **URL prefix `/api/nsdcc-workflow/`**: Distinct from `/api/workflows/` (Paperless automation) to avoid confusion.
