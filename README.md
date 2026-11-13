# NovaChat

NovaChat is a Django social networking application for sharing image-and-text posts, discovering and following people, and chatting in direct-message threads. It includes account registration and email verification, profile management, a paginated feed with likes and comments, and real-time chat over WebSockets.

## Features

- Account registration, login/logout, password reset, and email verification
- User profiles with bios, profile photos, websites, and follower/following lists
- Post creation with optional images, captions, likes, and comments
- Paginated social feed
- Direct-message inbox and chat threads
- Django admin interface

## Tech Stack

| Area | Technology |
|---|---|
| Language | Python; the repository does not pin a Python version. Use a version supported by Django 6.1 (Python 3.12 or newer). |
| Web framework | Django 6.1 |
| Database | SQLite (`db.sqlite3`) in the checked-in settings |
| Realtime | Django ASGI, Daphne, and Django Channels/`channels-redis` |
| Cache and channel storage | Redis via `django-redis` and `channels-redis` |
| Frontend | Django templates, HTML, CSS, and Tailwind CSS 2.2 |
| Email | Django email backend with optional Anymail/Brevo integration |
| Image uploads | Pillow |

`psycopg` and `dj-database-url` are also listed as dependencies, but the current settings do not configure PostgreSQL or read a database URL.

## Project Structure

```text
.
├── manage.py                 # Django management commands
├── Novachat/                 # Settings, root URLs, ASGI and WSGI entry points
├── users/                    # Accounts, profiles, follows, and email verification
├── posts/                    # Feed, posts, likes, and comments
├── chat/                     # Direct-message models, views, and WebSocket routing
├── requirements.txt          # Python dependencies
├── package.json              # Tailwind CSS build script
├── .env.example              # Environment variable template
├── media/                    # User and post uploads (runtime data)
└── db.sqlite3                # Local SQLite database (runtime data)
```

Each Django app also contains its migrations, templates, and tests; `users` and `chat` include static assets.

## Prerequisites

- Python 3.12 or newer, compatible with Django 6.1
- pip and Git
- Redis listening at `127.0.0.1:6379` for the configured cache and Channels backend
- Node.js and npm only if you need to rebuild the Tailwind CSS output
- Docker is optional as a convenient way to run Redis; the repository does not include Docker configuration

The project uses SQLite by default, so a separate database server is not needed for the current configuration.

## Local Setup & Installation

Clone the repository and enter its root directory:

```shell
git clone https://github.com/Devisinghd/NovaChat-Social-App.git
cd NovaChat-Social-App
```

Create and activate a virtual environment:

```shell
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```shell
source .venv/bin/activate
```

Install Python dependencies and create your local environment file:

```shell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```shell
cp .env.example .env
```

Edit `.env` before running the application. In particular, replace the `SECRET_KEY` placeholder with a new random value and configure the email provider if email verification is enabled. `.env.example` sets `DEBUG=False`; set `DEBUG=True` for local development if desired. Set `ALLOWED_HOSTS` to include the hostname you use when it is not `localhost` or `127.0.0.1`.

Start Redis in another terminal. If Docker is installed, for example:

```shell
docker run --rm --name novachat-redis -p 6379:6379 redis:7-alpine
```

The current settings connect to Redis at `127.0.0.1:6379`; there is no Redis URL environment variable in the project settings.

Run database migrations, optionally create an administrator, and start Django:

```shell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the feed and [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) for the administration site.

### Rebuilding Tailwind CSS (optional)

If you change the Tailwind input styles, install the Node dependencies and run the build from the repository root:

```shell
npm ci
npm run build
```

## Environment Variables

Settings load `.env` from the repository root. The table lists every variable read by `Novachat/settings.py`; values below are placeholders or safe defaults, not credentials.

| Variable | Required | Example / default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes for deployment | `<generate-a-unique-secret>` | Django signing key. The development fallback in settings is not suitable for deployment. |
| `DEBUG` | No | `True` in settings; `.env.example` sets `False` | Enables Django debug mode only when the value is exactly `True`. Keep disabled in deployment. |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated hostnames accepted by Django. |
| `EMAIL_BACKEND` | No | `anymail.backends.brevo.EmailBackend` in `.env.example`; otherwise Django SMTP backend | Django email backend. The example selects Anymail's Brevo backend. |
| `DEFAULT_FROM_EMAIL` | No | `NovaChat <noreply@example.com>` | Sender address for application email. Use an address verified by your provider. |
| `EMAIL_VERIFICATION` | No | `True` | Enables or disables email verification; compared case-insensitively with `true`. |
| `EMAIL_OTP_EXPIRY_MINUTES` | No | `10` | Lifetime of an email verification code, in minutes. |
| `BREVO_API_KEY` | If using Brevo | `<your-brevo-api-key>` | Brevo API credential used by Anymail. Keep it private and out of version control. |

`ALLOWED_HOSTS` is supported by settings but is not included in `.env.example`. The database and Redis connection addresses are currently configured in Python settings rather than through environment variables.

## Key Endpoints / Routes

| Method / path | Purpose |
|---|---|
| `GET /` | Main social feed |
| `/admin/` | Django administration |
| `/register/`, `/login/`, `/logout/` | Account registration and authentication |
| `/password_change/`, `/password_reset/`, `/reset/<uidb64>/<token>/` | Password management |
| `/email_verification/` and `/email_verification/...` | Email verification flow |
| `/profile/`, `/profile/<username>/`, `/edit/`, `/settings/` | View and edit profiles and account settings |
| `/toggle_follow/<username>/`, `/followers/<username>/`, `/following/<username>/` | Follow actions and relationship lists |
| `/posts/create/`, `/posts/feed/`, `/posts/like/` | Create posts, view the feed, and like posts |
| `/posts/<post_id>/comments/` | View and add comments for a post |
| `/chat/dashboard/`, `/chat/thread/<thread_id>/`, `/chat/direct/<user_id>/` | Inbox, direct-message thread, and open-or-create conversation |
| `WS /ws/chat/<thread_id>/` | Authenticated chat WebSocket route |

The WebSocket route is declared in `chat/routing.py`; the HTTP routes are assembled from the project and app URL configurations.

## Running Tests

Run the complete Django test suite from the repository root:

```shell
python manage.py test
```

To run tests for individual apps:

```shell
python manage.py test users posts chat
```

The tests use Django's built-in test runner. The `npm test` script is currently a placeholder and does not run tests.

## Notes

- Uploaded profile and post images are stored under `media/`.
- The repository includes no Dockerfile or Compose file.
- For a production deployment, configure a secure `SECRET_KEY`, `DEBUG=False`, appropriate `ALLOWED_HOSTS`, production-grade database/storage settings, and email credentials. The committed settings currently use local SQLite and Redis addresses.
