# Splitting hippocampus.college into two services

Goal: `hippocampus.college` serves **only the widgets**, so it can be handed to
anyone without explaining which half of the tracker works yet. The full tracker
moves to `app.hippocampus.college` (a pun that works: it is for college *apps*).

Both are the same repo and the same `Procfile`. The only difference is the
`WIDGETS_ONLY` environment variable, so widget improvements ship to both and
there is no second codebase to maintain.

| | Host | `WIDGETS_ONLY` | Database |
|---|---|---|---|
| Widgets | `hippocampus.college` | `True` | none |
| Tracker | `app.hippocampus.college` | unset | existing Postgres |

## What `WIDGETS_ONLY=True` changes

- Root URLconf becomes `college_app/widgets_only_urls.py` — only `/`, `/widgets/…`,
  and the `/time` + `/words` shortcuts exist. Admin, allauth, colleges,
  applications, activities and essays are **not routed**, so they 404.
- `college_app/widgets_only_templates/base.html` shadows `core/templates/base.html`,
  giving a navbar with no links except the wordmark. No sign-in, no account modal.
- `LoginRequiredMiddleware` is dropped (nothing to protect, and its redirects
  would point at an `/accounts/login/` that does not exist in this build).
- `/` renders `widgets/welcome.html`, the widgets landing page.

## Order matters

Do steps 1–3 **before** step 4. The point is to have the tracker working at its
new address, signed in and verified, before the apex stops pointing at it — so
there is no window where you cannot reach your own data.

### 1. Create the widgets service on Railway

New service, same GitHub repo (`ConfluxConflux/college-app-app`), branch `main`.

Variables:

    WIDGETS_ONLY=True
    TRACKER_URL=https://app.hippocampus.college
    ALLOWED_HOSTS=hippocampus.college,www.hippocampus.college
    SECRET_KEY=<a fresh one, not the tracker's>

Deliberately **do not** set `DATABASE_URL`, `GOOGLE_CLIENT_ID`,
`GOOGLE_CLIENT_SECRET`, or `EMAIL_APP_PASSWORD`. The widgets need none of them,
and without them this public service cannot reach real data. It falls back to a
throwaway SQLite file, which is fine: nothing is stored server-side — the word
counter and focus-write drafts live in the visitor's own browser.

Test it on the `*.up.railway.app` URL Railway gives you before touching DNS.

### 2. Give the tracker its new address

On the **existing** tracker service:

- Add the custom domain `app.hippocampus.college`.
- Append `app.hippocampus.college` to that service's `ALLOWED_HOSTS`.
  Skipping this gives `400 Bad Request`, not a helpful error.
- Add the CNAME Railway shows you at Namecheap.

### 3. Fix Google sign-in, then verify

In the Google Cloud console (the *College App App* project, which is under
chromaticconflux@gmail.com, not the primary address), add to the OAuth client:

- Authorized redirect URI: `https://app.hippocampus.college/accounts/google/login/callback/`
- Authorized JavaScript origin: `https://app.hippocampus.college`

**Then actually sign in at `https://app.hippocampus.college` and confirm it
works.** Do not continue until it does.

### 4. Flip the apex

- Remove `hippocampus.college` from the tracker service.
- Add `hippocampus.college` (and `www.`) to the widgets service.

`WwwRedirectMiddleware` already sends `www.hippocampus.college` to the bare host,
so the `www` record can point at the same place.

### 5. Tidy up

- In the tracker's Django admin, set the Sites record (id 1) domain to
  `app.hippocampus.college`. Migration `0011_update_site_domain` set it to the
  apex, which is now the widgets.
- Sanity-check `https://hippocampus.college/colleges/` returns **404**. If it
  returns a login redirect, the apex is still pointed at the tracker.

## Rolling back

Move the `hippocampus.college` domain back to the tracker service. The widgets
service holds no data, so deleting it loses nothing.

## Running the widgets build locally

    WIDGETS_ONLY=True DEBUG=True python3 manage.py runserver 8001
