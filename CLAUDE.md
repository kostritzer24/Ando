# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

El Patojismo (Centro Socioeducativo Lic. Magno Rudy Romero Arévalo) — academic management system: Django REST Framework backend (`backend/`) + Vue 3/TypeScript frontend (`frontend/`), contract-first via an OpenAPI schema the backend generates and the frontend turns into TypeScript types (never hand-written). Every requirement traces back to `docs/PROMPT_MAESTRO.md` (RF = functional requirement, RN = business rule, RNF = non-functional requirement, HU = user story) — never invent one that isn't documented there.

## Commands

### Backend (Django) — run from `backend/`

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py seed_demo              # idempotent demo data; prints seed user credentials (all use password CambiaEstaClave2026)
python manage.py runserver 8000
python manage.py check                  # quick sanity check
ruff check .                            # lint (line-length 100, rules E/F/I)
python -m pytest -q                     # full suite
python -m pytest apps/<app> -q          # one app
python -m pytest apps/<app>/tests/test_x.py::test_name -q   # single test
python -m pytest --cov=apps.<app>.domain --cov=apps.<app>.services --cov-report=term-missing   # coverage (only domain/ and services/ are gated, see .coveragerc)
```

**macOS-only gotcha:** any command touching PDF generation (`apps.documents`, `grading` boletín, `communication` reporte de conducta, `apps.reports`) needs `export DYLD_LIBRARY_PATH=/opt/homebrew/lib` in the same shell first — WeasyPrint needs Homebrew's Pango/Cairo, and Anaconda's Python ships its own conflicting `libcairo`/`libharfbuzz` that wins without this. Use `DYLD_LIBRARY_PATH` (priority), not `DYLD_FALLBACK_LIBRARY_PATH` — the fallback only fixes `import weasyprint`, not actual rendering (segfaults mid-PDF instead).

### Frontend (Vue 3 + Vite) — run from `frontend/`

```bash
npm install
cp .env.example .env                    # once; points at http://localhost:8000/api/v1
npm run dev                             # localhost:5173
npm run build                           # vue-tsc --noEmit && vite build
npm run lint
npm run typecheck                       # vue-tsc --noEmit
npm test                                # vitest run, unit tests for shared/components
npm run e2e                             # playwright, needs backend running with seed_demo + `npm run dev` up
npx playwright test e2e/<file>.spec.ts --workers=1   # one spec file at a time — see gotcha below
npm run types:generate                  # regenerates src/shared/types/api.ts against the live local backend — never hand-edit that file
```

**Playwright gotcha:** run one spec file at a time (`--workers=1`), not the whole `e2e/` suite — chaining specs trips the login rate limit (RNF-05: 10 attempts/min per IP, not relaxed in dev), producing false failures (redirect back to `/ingresar`) that look like bugs but aren't. If several specs fail with that exact symptom right after a burst of logins, re-run them in isolation before assuming a regression.

## Architecture

### Backend: one Django app per bounded context, layered internally

```
apps/<app>/
├── api/          views, serializers, urls — presentation only, no business logic
├── services/     one function per use case: orchestration, transactions, audit log writes
├── domain/       pure business rules (no Django import where possible) — the RN business rules live here
├── selectors/    read-optimized queries for reports/listings (first real consumer: apps/reports)
├── models.py     Django models; nearly everything extends core.BaseModel (public_id UUID, is_active soft-delete, created_at/updated_at)
├── templates/    HTML→PDF templates (WeasyPrint), only in apps that issue documents
└── tests/        + domain/tests/ for pure-rule unit tests
```

Enforced convention: a view never imports a model to write directly; a model never calls a service. Soft delete everywhere — nothing is ever hard-deleted (`is_active=False` via `BajaLogicaMixin` or a custom `perform_destroy`).

### Permission system (`apps.core.permissions`, `apps.core.api.mixins`)

- `PermisoPorArea`: default-deny (`DenyAll`); every `Role` has a `permissions` JSON map (`area → ver/editar/sin_acceso`), seeded in `apps/accounts/management/commands/seed_fase3.py` and documented in `docs/permisos-roles.md`. Every view declares `area = "..."`; GET needs `ver`, everything else needs `editar` unless the view overrides `nivel_requerido()`.
- `ScopedQuerysetMixin`: object-level scoping. Every list/detail view implements `scope_queryset(queryset, user)` — **never** compare a URL id against `request.user` directly; a wrong compare there leaks another family's/section's data.
- Recurring exception pattern (used for `ActivityTypeViewSet`, `JustificationTypeViewSet`, `ConductRuleArticleViewSet`): a role without area access to a whole catalog still needs read access to one field of it to use a form (e.g. a maestro guía picking a conduct-code article without administering the catalog). Solved by routing only `list`/`retrieve` through a different `area` in `get_permissions()`, keeping write on the catalog's own area — never by granting broader access.

### The `public_id` vs internal `id` trap

Every model exposes `public_id` (UUID) to the API; the internal `id` (integer PK) never leaves services/views. When a serializer's `SlugRelatedField` has already resolved to a model instance, be deliberate about which one you need: `.id` for FK shortcuts (`Model.objects.create(fk_id=...)`) or comparisons against a `.values_list("x_id", flat=True)` queryset; `.public_id` for anything sent back to a client or compared against something a client sent. Mixing them up produces either a silent 403 (comparing a UUID against a list of ints) or a SQLite `OverflowError` (a UUID landing in an `IntegerField`).

### PDF generation

Every issued PDF (constancias in `documents/`, boletín in `grading/`, reporte de conducta in `communication/`, the institutional reports in `reports/`) is rendered on demand from a Django HTML template with WeasyPrint — never stored and regenerated, never containing a digital signature (RN-15: two blank lines for an ink signature/stamp instead). `apps/reports/` reuses one generic tabular template (`reports/templates/reports/tabla.html`, dynamic columns via a custom `lookup` template filter) instead of one per report.

### Frontend structure

```
frontend/src/
├── app/            router.ts (role-gated routes per portal + global auth guard), http.ts (axios instance, JWT refresh interceptor)
├── features/<feature>/
│   ├── api/        thin wrappers over REST resources — standard CRUD goes through shared/api/resource.ts's crearRecursoCrud<T>(); custom actions (downloads, replies, non-CRUD POSTs) get a dedicated function
│   ├── components/ *Page.vue — often shared between two portals (e.g. CalendarioPage.vue used by both administrativo and operativo, gated by role inside the component) rather than duplicated
│   └── stores/      Pinia, only where state must survive cross-page navigation (authStore; portalStore holds the family's selected child)
├── pages/<portal>/  layout + top-level nav per portal: administrativo, operativo, publico
└── shared/types/    api.ts (generated, never hand-edit) + models.ts (hand-picked aliases, plus a few hand-written interfaces for endpoints that return a plain dict instead of a ModelSerializer output)
```

Three portals share one router, gated by `meta.roles` and a `beforeEach` guard reading `useAuthStore()`. `AdministrativoLayout`/`OperativoLayout` use the `AdminShell` sidebar; the public portal (`PublicoLayout`) uses `TopAppBar` + `BottomTabBar` + `DayTabs` — a mobile-first layout built early (Fase 3) against `docs/diseno/mockups/propuesta-b-tramite-claro.html` and left unused until the portal público was actually built.

### Where requirements and contracts live

- `docs/PROMPT_MAESTRO.md` — the only source of truth for requirements.
- `docs/api.md` — a **planning-era** API contract; repeatedly found stale against the real backend (missing endpoints, wrong parameter names — e.g. it once documented `?format=pdf`, which collides with a DRF-reserved query parameter and never reaches the view). Verify against `apps/<app>/api/urls.py`, not this doc.
- `docs/permisos-roles.md` — the authoritative role×area permission matrix.
- `docs/modelo-datos.md` — the full physical schema.
- `docs/adr/` — architecture decisions (foundational libraries, PDF/QR approach, audit log format, etc.).
- `docs/fase-N-cierre.md` (backend) / `docs/fase-N-frontend-cierre.md` (frontend, or combined backend+frontend from Fase 10 onward) — one closing document per phase: what was built, real bugs found and fixed, how it was verified live. `docs/pendiente-frontend.md` is the live tracker of frontend progress across phases — read it plus the latest closure doc before assuming project state.

### Git workflow

One branch per phase, each branching from the *previous phase's* branch, not from `main` (`fase-01-plan-maestro` → `fase-02-...` → … ). `main` is deliberately frozen (end of Fase 3) pending a full review — nothing has been merged into it.

## Testing conventions

- Test names carry the RF/RN/HU code they verify (`test_rf24_...`, `test_rn16_...`) — the traceability matrix must be reconstructible from the code alone.
- Every API resource's tests include at least one unauthorized-access case (wrong role, or right role but wrong object scope).
- The 80% coverage gate (see `backend/.coveragerc`) applies only to `domain/` and `services/`; `api/`, `selectors/`, `models.py` are measured but not gated.
- Factories live in `apps/<app>/tests/factories.py` (factory_boy); lookup-table-style models (Role, Course, DocumentType, ActivityType) use `django_get_or_create` to avoid unique-constraint collisions across tests reusing the same name.
- A phase is not done when its automated tests pass. Live verification is required before closing any phase: reset the db (`rm db.sqlite3 && python manage.py migrate && python manage.py seed_demo`), run the backend for real, and run Playwright against a real Chromium browser. E2E specs live in `frontend/e2e/`, one file per phase.
