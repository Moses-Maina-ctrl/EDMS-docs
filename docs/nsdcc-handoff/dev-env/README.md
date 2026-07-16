# Local verification environment

One-time bring-up (from this directory, Docker Desktop running):

```bash
# 1. Build the image from your branch (MUST be via git archive — see handoff README §5)
git -c core.autocrlf=false archive <your-branch> | docker build -t edms-local:stack -

# 2. Start (redis + webserver, sqlite, port 8000; superuser admin/admin auto-created)
docker compose up -d
# wait ~60s for migrations on first boot; then http://localhost:8000

# 3. Create the NSDCC groups and seed demo data (first boot only)
docker exec edms-dev-webserver-1 python3 manage.py create_workflow_groups
docker cp seed_demo.py edms-dev-webserver-1:/tmp/seed_demo.py
docker exec edms-dev-webserver-1 sh -c "python3 manage.py shell < /tmp/seed_demo.py"
# ^ prints API tokens for pa_office / registry_ann / jmwangi

# 4. Grant the demo users baseline UI permissions (they're created bare)
docker exec edms-dev-webserver-1 python3 -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','paperless.settings')
django.setup()
from django.contrib.auth.models import Permission, User
codes = ['view_uisettings','add_uisettings','change_uisettings','view_document','view_documenttype','view_correspondent','view_tag','view_storagepath','view_savedview','view_paperlesstask','view_note']
perms = list(Permission.objects.filter(codename__in=codes))
for uname in ('pa_office','registry_ann','jmwangi','kotieno'):
    User.objects.get(username=uname).user_permissions.add(*perms)
print('PERMS OK')"
```

Users (password `demo1234`): `pa_office` (PA), `registry_ann` (Registry), `jmwangi`,
`kotieno` (GeneralStaff). Superuser: `admin`/`admin`.

Seeded workflows: overdue (assigned jmwangi), pending_action (jmwangi), reassigned
(kotieno→jmwangi), received (unassigned), actioned. `jmwangi`'s inbox shows exactly 3.

After a code change: rebuild the image (step 1) and `docker compose up -d` — the sqlite
volume persists, no re-seeding needed.

Headless screenshots without interactive login: add
`PAPERLESS_AUTO_LOGIN_USERNAME: <username>` to the webserver environment in
`docker-compose.yml`, `docker compose up -d`, then

```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless --disable-gpu \
  --hide-scrollbars --window-size=1440,900 --virtual-time-budget=20000 \
  --screenshot=out.png "http://localhost:8000/workflow/inbox"
```

Remove the env var (and `up -d` again) when done.
