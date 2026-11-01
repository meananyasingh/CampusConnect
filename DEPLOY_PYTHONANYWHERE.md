# Demo deployment on PythonAnywhere

This publishes CampusConnect at `https://<username>.pythonanywhere.com` on PythonAnywhere's free plan. Django serves the API, the admin, uploaded files, and the built React app from that single address. The existing SQLite database and uploaded files are copied as-is, so the demo starts with your current data.

Throughout this guide, replace `<username>` with your PythonAnywhere username.

## 1. Prepare the package on your computer

Build the frontend, then package the project without the OS-specific, generated, and private files. Run in PowerShell from the folder that contains the `CampusConnect` project folder (for example `E:\CampusConnect`):

```powershell
npm --prefix CampusConnect\frontend run build

tar -czf campusconnect-deploy.tar.gz --exclude=.venv --exclude=node_modules --exclude=staticfiles --exclude=__pycache__ --exclude=.git --exclude=CampusConnect/.env --exclude="Campus Connect Plan" --exclude="*Complete Codex Development Prompt.md" CampusConnect
```

This creates `campusconnect-deploy.tar.gz` next to the project folder.

## 2. Create the account and upload

1. Sign up for a free **Beginner** account at https://www.pythonanywhere.com/. Your username becomes part of the link.
2. Open the **Files** tab and upload `campusconnect-deploy.tar.gz` into `/home/<username>/`.

## 3. Install the backend

Open the **Consoles** tab, start a **Bash** console, and run:

```bash
tar -xzf campusconnect-deploy.tar.gz
cd ~/CampusConnect/backend
python3.11 -m venv ~/.virtualenvs/campusconnect
source ~/.virtualenvs/campusconnect/bin/activate
pip install -r requirements.txt
```

If `mysqlclient` fails to install, skip it because the demo uses SQLite:

```bash
grep -v mysqlclient requirements.txt > /tmp/requirements.txt
pip install -r /tmp/requirements.txt
```

## 4. Configure the environment

Generate a secret key and copy the output:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Create `~/CampusConnect/.env` (for example with `nano ~/CampusConnect/.env`) containing:

```text
DJANGO_SECRET_KEY=<paste-the-generated-key>
DEBUG=False
ALLOWED_HOSTS=<username>.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://<username>.pythonanywhere.com
CORS_ALLOWED_ORIGINS=https://<username>.pythonanywhere.com
FRONTEND_URL=https://<username>.pythonanywhere.com
BEHIND_HTTPS_PROXY=True
```

Then prepare the database and Django's static files:

```bash
cd ~/CampusConnect/backend
python manage.py migrate
python manage.py collectstatic --noinput
```

## 5. Create the web app

On the **Web** tab:

1. Click **Add a new web app** → **Next** → **Manual configuration** → **Python 3.11**.
2. Under **Code**, set **Source code** to `/home/<username>/CampusConnect/backend`.
3. Under **Virtualenv**, enter `/home/<username>/.virtualenvs/campusconnect`.
4. Click the **WSGI configuration file** link, delete everything in it, and replace it with:

   ```python
   import os
   import sys

   path = "/home/<username>/CampusConnect/backend"
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

5. Under **Static files**, add two entries:

   | URL | Directory |
   |---|---|
   | `/static/` | `/home/<username>/CampusConnect/backend/staticfiles` |
   | `/media/` | `/home/<username>/CampusConnect/backend/media` |

6. Under **Security**, turn on **Force HTTPS**.
7. Click the green **Reload** button at the top.

Open `https://<username>.pythonanywhere.com`. Check `https://<username>.pythonanywhere.com/api/health/` if the page does not load.

## Updating the demo later

After changing code, repeat step 1 and upload the new package. In a Bash console, extract it over the existing copy while keeping the server's database, uploads, and `.env`:

```bash
cd ~
tar -xzf campusconnect-deploy.tar.gz --exclude=CampusConnect/backend/db.sqlite3 --exclude=CampusConnect/backend/media --exclude=CampusConnect/.env
cd ~/CampusConnect/backend
source ~/.virtualenvs/campusconnect/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

Then click **Reload** on the **Web** tab.

## Demo limitations

- **Emails are not delivered.** Password-reset and activation emails are written to the **Server log** on the Web tab. Open it to copy a link during the demo.
- **Uploaded files are public by link.** Anyone with a resume or document URL can open it. Use demo data rather than real student files.
- **Keep the app alive.** Free web apps stop after one month unless you click **Run until 1 month from today** on the Web tab. PythonAnywhere emails a reminder a week before.
- **Errors are logged, not shown.** With `DEBUG=False`, check the **Error log** on the Web tab when something fails.
