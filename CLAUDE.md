# CLAUDE.md — Hippocampus Codebase Reference

## Project Overview

Personal college application tracker. Django 6 + htmx 2 + Alpine.js 3 + Bulma 1.0. No build step. Deployed on Railway (PostgreSQL in prod, SQLite locally). Sole intended user is Jacob. Live at hippocampus.college.

**Kathy** is Jacob's college counselor consultant. Her top priority: activities list manager that avoids redundant entry across UC, Common App, and MIT. The Compare and Brainstorm tabs exist to solve this — but the right interface hasn't been found yet. Activities work is the most important unsolved problem.

---

## App Structure

| App | Responsibility |
|-----|----------------|
| `college_app` | Settings, root URLs, `applications_urls.py` |
| `core` | `Applicant`, `CoreActivity` models; base templates; auth middleware; dashboard |
| `colleges` | `College` (canonical/IPEDS), `UserCollege` (per-user); college list + applications views |
| `activities` | `UCEntry`, `CommonAppActivity`, `CommonAppHonor`, `MITEntry`; per-format activity views |
| `supplements` | `SupplementEssay`, `UCPersonalInsightQuestion`, `CommonAppEssay`, `EssayCategory` |
| `widgets` | Stateless utility pages: time calculator, word counter, focus write, advice, resources |

---

## Key Models

### `core.Applicant`
- `user` (OneToOne → auth.User, nullable), `first_name`, `last_name`, `email`, `profile_picture`, `brainstorm`
- All application data belongs to an Applicant, not directly to a User.

### `core.CoreActivity`
- Hub model for one real-world activity. Format-specific entries (UCEntry, CommonAppActivity, etc.) FK back here.
- `applicant`, `name`, `full_description`, `personal_notes`, `order`
- `grade_9/10/11/12` (BooleanField), `hours_per_week`, `weeks_per_year` (CharField)
- Ordering: `['order', 'name']`

### `colleges.College`
- Canonical college data from IPEDS. Shared across all users, never owned by an applicant.
- Key fields: `unitid` (unique), `name`, `city`, `state`, `acceptance_rate`, `sat_avg`, `app_platform`, deadlines, costs, `proof_acceptances` (int — proxy for relevance, used for sorting).

### `colleges.UserCollege`
- Per-user college record. FK to `College` (nullable — freeform entries have no canonical match).
- **Every canonical field has a `_override` counterpart** (e.g. `city_override`, `sat_avg_override`).
- **Properties with setters** implement fallback: `uc.city` returns `city_override` if set, else `college.city`.
- **NEVER set `_override` fields directly.** Use property setters: `uc.city = 'Boston'` routes to the right field. Call `.save()` after.
- Special alias: `uc.terms` → `academic_calendar` (legacy name kept).
- `uc.name` property returns `display_name or college.name`.
- `apply_status` choices: `not_applying`, `considering`, `applying`, `applied`, `deferred`, `waitlisted`, `rejected`, `accepted` (+ hidden legacy: `likely`, `unlikely`, `enrolled`, `withdrawn`)
- Status display uses `.status_color` property → CSS class like `pill-applying`.
- Difficulty display uses `.difficulty_color` property → inline CSS string.

### `activities.UCEntry`
- Up to 20 per applicant. FK to `CoreActivity` (nullable).
- `category`: `award`, `edu_prep`, `extracurricular`, `volunteer`, `work`, `coursework`
- `name`, `background` (250ch), `description` (350ch), grade booleans, level booleans, `estimator_data` (JSONField)

### `activities.CommonAppActivity`
- Up to 10. `activity_type` (26 choices), `position` (150ch), `organization` (100ch), `description` (150ch)
- `hours_per_week`, `weeks_per_year` are IntegerField (unlike UCEntry which uses CharField)

### `activities.CommonAppHonor`
- Up to 5. `title`, grade booleans, level booleans (school/state_regional/national/international)

### `activities.MITEntry`
- Category limits: `job` 5, `activity` 4, `summer` 6, `scholastic` 5, `non_scholastic` 5
- `org_name`, `role_award`, `participation_period`, `description` (40 words enforced at form layer)

### `supplements.SupplementEssay`
- FK to `UserCollege`, FK to `EssayCategory` (nullable)
- `prompt`, `word_limit`, `char_limit`, `response`, `status` (wip/done/maybe), `sort_order`
- `.word_count`, `.char_count` are properties.

### `supplements.UCPersonalInsightQuestion`
- 8 per applicant (auto-created in `applications_uc` view). `question_number` 1–8.
- `.prompt` property returns from `UC_PIQ_PROMPTS` list.

### `supplements.CommonAppEssay`
- OneToOne with Applicant. `prompt_choice` (1–7 or null), `response`, `status`.

---

## URL Namespaces

| Namespace | Prefix | Notes |
|-----------|--------|-------|
| `core` | `/` | `landing`, `home`, `profile`, `core_activity_cell`, `core_activity_add/delete`, `core_activity_uc/ca/honor/mit_cell` |
| `colleges` | `/colleges/` | `list`, `list_all`, `add`, `add_row`, `detail`, `delete`, `edit_cell`, `update`, `search_suggestions`, `quick_add`, `json` |
| `applications` | `/applications/` | `home` (MIT/Common/individual), `uc`, `common` |
| `activities` | `/activities/` | `home_uc/common/mit/compare/brainstorm`, cell edit/delete for all 4 entry types, export endpoints |
| `supplements` | `/essays/` | `home`, `essay_save/status/focus/category`, `uc_piq_save/status`, `common_essay_save/status` |
| `widgets` | `/widgets/` | `home`=estimator, `focus_write`, `word_counter`, `advice`, `resources` |

---

## Template Structure

### Two base templates

**`core/templates/base.html`** — used by all main app views.
- Bulma CDN, Open Sans + Libre Baskerville (Google Fonts), `app.css`, htmx 2.0.4, Alpine.js 3.14.8.
- Full navbar. `{% block content %}` inside `<section class="section"><div class="container is-fluid">`.
- CSRF token auto-injected for all htmx requests via `htmx:configRequest` listener.

**`core/templates/focus_base.html`** — no navbar, distraction-free.
- Same CSS/JS stack. Used by `supplements/focus.html` and all `widgets/` templates.

### Partial templates (no `extends`, returned by htmx):
- `colleges/_college_row.html` — saved row after edit
- `colleges/_college_row_with_tracker.html` — row + platform tracker (returned after status changes)
- `colleges/_cell_edit.html` / `_cell_edit_select.html` — row with active input
- `colleges/_college_table.html` — full table body (htmx table refresh)
- `colleges/_search_suggestions.html` — typeahead results
- `core/_core_activity_row.html` — centralized activities table row
- `activities/_uc_row.html`, `_ca_row.html`, `_honor_row.html`, `_mit_row.html` — format-specific rows
- `activities/_uc_empty_row.html`, `_ca_empty_row.html` — empty slot placeholders

---

## htmx Inline Editing — TWO DISTINCT PATTERNS

### Pattern A: Alpine-driven (all activity row partials)

Used in `_core_activity_row.html`, `_uc_row.html`, `_ca_row.html`, `_honor_row.html`, `_mit_row.html`.

```html
<td x-data="{ e:false, v:'{{ entry.name|escapejs }}' }">
  <span x-show="!e" @click="e=true; $nextTick(()=>$refs.i.focus())" x-text="v||'—'"></span>
  <input x-show="e" x-ref="i" class="input is-small" name="value" x-model="v"
    hx-post="{% url 'activities:uc_cell' entry.pk 'name' %}"
    hx-trigger="blur"
    hx-swap="none"
    @blur="e=false">
</td>
```

- `hx-trigger="blur"` saves on focus-out; `hx-swap="none"` means htmx fires but does NOT touch the DOM (Alpine already has the value).
- `@blur="e=false"` switches back to view mode.
- Textareas also use `hx-trigger="blur, input delay:1500ms"` for autosave while typing.
- **No submit/cancel buttons. Enter or blur saves. Escape cancels.**
- The `editing` context variable passed by views (`_core_row_ctx(activity, editing=field)`) is **never referenced in any template** — it is vestigial dead code. Don't rely on it or add logic around it.

### Pattern B: Server-driven row swap (college list table only)

Used in `colleges/_cell_edit.html` and `_cell_edit_select.html`.

- Click on a cell → GET to `colleges:edit_cell pk field` → server returns full `<tr>` with input in that cell.
- Input uses `onblur="this.form.requestSubmit()"` (plain JS, not Alpine).
- POST saves → server returns saved `<tr>` via `_college_row.html`.
- Escape: `htmx.ajax('GET', window.location.href, '#college-table-wrapper')` reloads the whole table.
- The edit form *replaces* the entire row, no Alpine involved.

---

## Context & Auth

**`applicant` context processor**: injects `applicant` (the `Applicant` instance) into every template. Use `applicant` in templates, `request.user.applicant` in views.

**`LoginRequiredMiddleware`**: all URLs require auth except:
- `/` (landing), `/accounts/` (allauth), `/admin/`, `/widgets/` (all widgets are public), `/time`, `/words`, `/are-you-sure`
- `/switch-applicant/` is exempt **only when `DEBUG=True`**.

**New user signup**: `SocialAccountAdapter` redirects new social logins to `/are-you-sure` before creating an account.

**Dev shortcut**: `/switch-applicant/<pk>/` logs in as the user linked to that Applicant. It grants a session for any applicant with no credentials, so it is **routed only under `DEBUG`** (`core/urls.py`) and the view re-checks `settings.DEBUG` independently. Never register this route unconditionally.

**Ownership**: every per-applicant object must be fetched with `get_object_or_404(Model, pk=pk, applicant=request.user.applicant)`. A bare `pk=pk` lookup is an IDOR — the app is multi-user.

---

## CSRF

Handled globally in both base templates via `htmx:configRequest`. Do NOT add `{% csrf_token %}` inside htmx-targeted forms — it's already covered. Standard non-htmx `<form>` POSTs still need `{% csrf_token %}`.

---

## Styling

- **Bulma 1.0** from CDN. Primary color overridden to teal (`--bulma-primary-h: 173deg`).
- Custom CSS: `core/static/css/app.css`. Always light mode (overrides Bulma dark defaults).
- Background: radial gradient on `html`, transparent body.
- Status pills: CSS classes `pill-applying`, `pill-accepted`, etc. defined in `app.css`.
- `{{ college|getfield:field_name }}` — template tag in `college_tags.py` for dynamic attribute lookup.

---

## Behavioral Rules

- **No submit/cancel buttons on inline inputs.** Submit on Enter/blur, Escape cancels.
- When modifying `UserCollege` fields, always use property setters, never `_override` fields directly.
- Check `if request.headers.get('HX-Request')` to return partials vs. full pages.
- `HX-Trigger` response header fires cross-component events (`confetti` on add, `college-added` after quick-add).

---

## Known Issues & Debt

- **backup-cron Railway service is crashing in production.** The `backup_db` management command emails a DB dump; the Railway cron service running it has crashed. Needs investigation.
- The `editing` context variable in `_core_row_ctx()` and format-specific cell views is passed but never consumed. Dead code.
- `college_json` and `college_update` views (Tabulator-era JSON endpoints) may be unused now that the table is htmx-driven.
- Activities Compare/Brainstorm views exist but the interface hasn't found the right UX for reducing redundant entry. This is the main unsolved product problem.

---

## Verification Protocol

Before declaring any fix done: specify exactly what to test and what the correct behavior looks like. Never say "this should fix it" without a test case. I cannot run the server — Jacob must verify.
