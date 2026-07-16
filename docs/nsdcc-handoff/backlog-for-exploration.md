# Backlog & Known Issues — for exploration, NOT to fix unprompted

Context the implementer should know. Raise these with the repo owner when relevant;
only act on them if a phase PRD explicitly includes them or the owner asks.

## Product / backend gaps (found by comparing the backend to the business process deck)

1. **No "Registry Review & Close" lifecycle step.** The process deck (IDMS Physical
   Document Process Flow v4) ends with Registry reviewing an ACTIONED document and
   either CLOSING it or returning it for rework (with a re-action email). The backend
   has no `closed` status, no close/return endpoints, and no rework notification — the
   lifecycle ends at `actioned`. Needs a product decision + backend work. Suggest filing
   as its own issue if the team confirms the deck is the target behavior.
2. **Status terminology mismatch.** Deck: UPLOADED → REGISTERED → ACTIONED → CLOSED.
   Backend: `received → pending_action → reassigned → actioned` (+ `overdue`).
   Functionally similar until step 4, but client-facing wording won't match the deck.
   Product decision; frontend uses backend `status_display` everywhere, so a backend
   rename would flow through automatically.
3. **`summary` field had no write endpoint.** Phase 5 adds a minimal `summarise/`
   endpoint. If the team prefers a different shape (e.g. one combined registry-update
   endpoint), align during review of the phase-5 PR.
4. **Unworkflowed documents are invisible to NSDCC endpoints.** If the PA dismisses the
   initiate modal, the document exists in paperless but appears in no NSDCC inbox or
   registry list. The deck implies Registry should see every upload. Possible fix: a
   registry filter/tab for "documents without workflows" (needs a new endpoint or a
   documents-API query). Product decision.

## Repo / CI debt (pre-existing, team is aware — do NOT fix in feature PRs)

5. **`Lint (prek)` job fails repo-wide** (`--all-files` vs ~150 old violations: ruff
   import style, prettier on docs, EOF/whitespace, yamlfmt). A dedicated mechanical
   cleanup PR would fix it; keep it out of feature branches.
6. **Pre-existing backend test failures**: `test_index` (expects
   `frontend/en-US/manifest.webmanifest` path) and `test_api_schema` (drf-spectacular
   "unable to guess serializer" warnings for every `nsdcc_workflows` APIView — fixable
   by adding `serializer_class`/`@extend_schema` annotations to those 12 views; would
   make the schema job meaningful again).
7. **GitHub issue #45 body is a duplicate of #44's** (copy-paste error at issue-creation
   time). `phase-5-workflow-detail.md` is the authoritative spec; fixing the issue body
   to match is worthwhile housekeeping.
8. **No `.gitattributes`.** On Windows checkouts (`autocrlf=true`) every text file goes
   CRLF, which breaks Docker image builds from the working tree (shebang `\r`, exit 127)
   and would break s6 runtime scripts. The git-archive build recipe (README §5) is the
   workaround; a `.gitattributes` forcing LF on `*.py`, `*.sh`, and `docker/**` is the
   real fix. Coordinate with the team before adding (it re-normalizes files).
9. **DevOps: `create_workflow_groups` is not run by container init** (planning doc
   "Issue 9", never filed on GitHub). Fresh deployments must run it manually; add it to
   the s6 init scripts / entrypoint next to `migrate`.
10. **Docker Desktop on the dev machine drops its engine pipe occasionally** — relaunch
    Docker Desktop and retry; nothing repo-related.
11. **Pulling `ghcr.io/moses-maina-ctrl/edms:latest` requires a token with
    `read:packages`** — building locally from git archive avoids it.

## Documentation

12. Keep `docs/nsdcc-workflow.md` "What Remains" current as phases merge; it drives
    expectations for the rest of the team.
