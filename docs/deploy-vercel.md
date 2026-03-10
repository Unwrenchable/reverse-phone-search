# Deploying to Vercel

This guide walks through every step required to deploy **reverse-phone-search** on Vercel from a clean clone. The app is a Python/Flask application; Vercel runs it as a serverless function using its Python runtime.

---

## How it works on Vercel

| Aspect | Detail |
|---|---|
| Runtime | Python (auto-detected from `requirements.txt`) |
| Entry point | `api/index.py` → exports the Flask `app` WSGI object |
| Routing | `vercel.json` rewrites all paths to the Flask app |
| Database | SQLite, stored in `/tmp` (ephemeral per instance) |

> **Note on the database:** Vercel's serverless filesystem is ephemeral. The SQLite database is re-seeded with sample data on every cold start. This is fine for a demo app; for production persistence use an external database service (e.g., PlanetScale, Supabase, Turso).

---

## Prerequisites

- A [Vercel account](https://vercel.com/signup) (free tier works)
- The repository forked or pushed to GitHub / GitLab / Bitbucket

---

## Option A — Deploy from the Vercel Dashboard (recommended)

1. Go to <https://vercel.com/new> and sign in.
2. Click **Import Git Repository** and select `reverse-phone-search`.
3. On the **Configure Project** screen set:

   | Setting | Value |
   |---|---|
   | **Framework Preset** | `Other` |
   | **Root Directory** | *(leave blank — project root)* |
   | **Build Command** | *(leave blank — no build step required)* |
   | **Output Directory** | *(leave blank)* |
   | **Install Command** | *(leave blank — Vercel runs `pip install -r requirements.txt` automatically)* |

4. Expand **Environment Variables** and add:

   | Name | Value | Required |
   |---|---|---|
   | `DB_PATH` | `/tmp/phone_search.db` | **Yes** |

   > Without `DB_PATH`, the app tries to write the database to the read-only working directory and will crash on first request.

5. Click **Deploy**.  
   Vercel builds the project and gives you a `*.vercel.app` URL within a minute or two.

---

## Option B — Deploy via the Vercel CLI

```bash
# 1. Install the CLI globally (once)
npm install -g vercel

# 2. From the repository root, start an interactive deployment
vercel

# Follow the prompts:
#   Set up and deploy → Y
#   Which scope → (choose your account/team)
#   Link to existing project? → N (first time)
#   Project name → reverse-phone-search (or any name)
#   In which directory is your code located? → ./
#   Want to modify settings? → N

# 3. Add the required environment variable
vercel env add DB_PATH
# When prompted, enter: /tmp/phone_search.db
# Select environments: Production, Preview, Development

# 4. Re-deploy to apply the env var, or deploy to production
vercel --prod
```

After `vercel --prod` completes you will see a `Production` URL.

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DB_PATH` | **Yes** (on Vercel) | `phone_search.db` | Filesystem path for the SQLite database. Must point to a writable location; use `/tmp/phone_search.db` on Vercel. |

There are no other environment variables. The app has no external API keys or secrets.

---

## Preview and production deployments

| Trigger | Result |
|---|---|
| Push to `main` branch | **Production** deployment (your primary `*.vercel.app` URL) |
| Open a Pull Request | **Preview** deployment (unique URL per PR, shown as a PR status check) |
| Push to any other branch | **Preview** deployment |

Each preview URL is isolated and fully functional with its own database state seeded from sample data.

---

## Troubleshooting

### `OperationalError: unable to open database file`

**Cause:** `DB_PATH` is not set, so the app tries to create `phone_search.db` in the read-only working directory.  
**Fix:** Add `DB_PATH=/tmp/phone_search.db` to your Vercel environment variables (see step 4 of Option A or the `vercel env add` step of Option B) and redeploy.

---

### `ModuleNotFoundError: No module named 'flask'` (or `phonenumbers`)

**Cause:** `requirements.txt` was not found or not installed.  
**Fix:** Ensure `requirements.txt` is present in the repository root and is committed to Git. Vercel installs it automatically during the build phase.

---

### 500 error on the `/search` route

**Cause:** Most likely the database was not initialised.  
**Fix:** Verify `DB_PATH=/tmp/phone_search.db` is set in Vercel → Project Settings → Environment Variables, then trigger a fresh deployment (redeploy from the Vercel dashboard or run `vercel --prod` again).

---

### Templates / static files not found (404 on CSS or JS)

**Cause:** Vercel's Python runtime may fail to locate the `templates/` or `static/` directories if the project root is not on `sys.path`.  
**Fix:** This is handled automatically by `api/index.py`, which adds the project root to `sys.path` before importing the Flask app. If you move or rename `api/index.py`, update the `sys.path.insert` call accordingly.

---

## Local development (for comparison)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask development server
python app.py
```

The app is then available at <http://127.0.0.1:5000>.
