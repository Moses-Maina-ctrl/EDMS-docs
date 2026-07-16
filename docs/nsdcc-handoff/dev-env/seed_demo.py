# Demo seed for NSDCC workflow evaluation. Idempotent-ish: safe to re-run.
# Run inside the container:
#   python3 manage.py shell < /tmp/seed_demo.py
import datetime
import uuid

from django.contrib.auth.models import Group, User

from documents.models import Document, DocumentType
from nsdcc_workflows.models import DocumentWorkflow, DocumentWorkflowAction

TODAY = datetime.date.today()


def user(username, group_name, first, last):
    u, _ = User.objects.get_or_create(
        username=username,
        defaults={"first_name": first, "last_name": last, "email": f"{username}@nsdcc.example"},
    )
    u.set_password("demo1234")
    u.save()
    g = Group.objects.get(name=group_name)
    u.groups.add(g)
    return u


def doc(title, dtype=None):
    d = Document.objects.filter(title=title).first()
    if d:
        return d
    return Document.objects.create(
        title=title,
        content=f"{title} (demo)",
        checksum=uuid.uuid4().hex,
        mime_type="application/pdf",
        document_type=dtype,
    )


def wf(document, **kw):
    w = DocumentWorkflow.objects.filter(document=document).first()
    if w:
        return w
    return DocumentWorkflow.objects.create(document=document, **kw)


pa = user("pa_office", "PA", "Pauline", "Achieng")
reg = user("registry_ann", "Registry", "Ann", "Wanjiru")
staff1 = user("jmwangi", "GeneralStaff", "James", "Mwangi")
staff2 = user("kotieno", "GeneralStaff", "Kevin", "Otieno")

corr = DocumentType.objects.get_or_create(name="Correspondence")[0]
memo = DocumentType.objects.get_or_create(name="Internal Memo")[0]

# 1. Overdue, assigned to jmwangi (proves the inbox overdue fix)
d1 = doc("Budget circular FY2026-27", corr)
w1 = wf(
    d1,
    confidentiality="internal",
    status=DocumentWorkflow.Status.OVERDUE,
    deadline=TODAY - datetime.timedelta(days=5),
    instruction="Circulate to finance and confirm allocations before the deadline.",
    assigned_to=staff1,
    uploaded_by=pa,
    is_overdue=True,
    serial_number="NSDCC/2026/0114",
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w1, action_type="uploaded", performed_by=pa
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w1, action_type="assigned", performed_by=reg, assigned_to=staff1
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w1, action_type="overdue_flagged"
)

# 2. Pending action, assigned by registry
d2 = doc("Letter from Ministry of Health", corr)
w2 = wf(
    d2,
    confidentiality="confidential",
    status=DocumentWorkflow.Status.PENDING_ACTION,
    deadline=TODAY + datetime.timedelta(days=2),
    instruction="Review and draft a response for CEO signature by Friday.",
    assigned_to=staff1,
    uploaded_by=pa,
    serial_number="NSDCC/2026/0117",
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w2, action_type="uploaded", performed_by=pa
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w2, action_type="assigned", performed_by=reg, assigned_to=staff1
)

# 3. Reassigned (delegated from kotieno to jmwangi)
d3 = doc("Board meeting minutes - June", memo)
w3 = wf(
    d3,
    confidentiality="internal",
    status=DocumentWorkflow.Status.REASSIGNED,
    deadline=TODAY + datetime.timedelta(days=7),
    instruction="File and extract action items for the operations team.",
    assigned_to=staff1,
    uploaded_by=pa,
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w3, action_type="uploaded", performed_by=pa
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w3, action_type="assigned", performed_by=reg, assigned_to=staff2
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w3,
    action_type="delegated",
    performed_by=staff2,
    assigned_from=staff2,
    assigned_to=staff1,
    comment="On leave this week - please handle.",
)

# 4. Received (unassigned) - must NOT appear in anyone's inbox
d4 = doc("Vendor invoice batch #88")
wf(d4, confidentiality="public", status=DocumentWorkflow.Status.RECEIVED, uploaded_by=pa)

# 5. Actioned - must NOT appear in the inbox
d5 = doc("Staff training request", memo)
w5 = wf(
    d5,
    confidentiality="internal",
    status=DocumentWorkflow.Status.ACTIONED,
    deadline=TODAY - datetime.timedelta(days=1),
    instruction="Approve and forward to HR.",
    assigned_to=staff1,
    uploaded_by=pa,
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w5, action_type="assigned", performed_by=reg, assigned_to=staff1
)
DocumentWorkflowAction.objects.get_or_create(
    workflow=w5, action_type="actioned", performed_by=staff1, comment="Approved and sent to HR."
)

from rest_framework.authtoken.models import Token

for u in (pa, reg, staff1):
    t, _ = Token.objects.get_or_create(user=u)
    print(f"TOKEN {u.username} {t.key}")

print("SEED OK:", DocumentWorkflow.objects.count(), "workflows")
