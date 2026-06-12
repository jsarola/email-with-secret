# Plan: email-with-secret

## Context
Build a Python CLI tool that reads recipient data from a CSV file, creates a OneTimeSecret link for each recipient's secret data, renders a Jinja2 email template with the generated link, and sends the email via Python's smtplib. The goal is a self-contained, config-driven script suitable for sending personalised secrets (passwords, tokens, etc.) to a list of people.

---

## Files to Create

```
email-with-secret/
├── send.py              # main entry point
├── config.ini           # SMTP + OTS configuration (not committed with real creds)
├── config.ini.example   # safe example config to commit
├── example.csv          # sample CSV with one row
├── templates/
│   └── default.html.j2  # default Jinja2 email template
└── requirements.txt
```

---

## Implementation Plan

### 1. `config.ini` / `config.ini.example`

INI format (parsed with `configparser`):

```ini
[smtp]
host = smtp.example.com
port = 587
username = user@example.com
password = secret
from = user@example.com
use_tls = true

[onetimesecret]
url = https://onetimesecret.com
api_user = user@example.com
api_key = your_api_key
```

- `url` can be swapped to `https://secret.example.com` for self-hosted instances.
- `config.ini.example` contains placeholder values and is safe to commit; `config.ini` holds real creds and is gitignored.

### 2. `example.csv`

Semicolon-delimited, no header row:

```
1;John Ripper;123456789;john.ripper@mail.com
```

Fields: `id;name;data;email`

### 3. `templates/default.html.j2`

Jinja2 template exposing `{{ name }}`, `{{ secret_url }}`, `{{ data }}` (raw, omit if only URL is needed).

### 4. `requirements.txt`

```
jinja2
requests
```

`smtplib` and `configparser` are stdlib — no extra installs needed.

### 5. `send.py` — Core Logic

#### CLI (argparse)
- `--file FILE` (required) — path to CSV
- `--template TEMPLATE` (required) — path to Jinja2 template file
- `--id ID` (optional) — only process rows whose first field matches this value
- `--config CONFIG` (optional, default `config.ini`) — path to config file

#### Flow per CSV row
1. Parse CSV with `csv.reader(delimiter=';')`; fields: `id, name, data, email`
2. If `--id` given, skip rows where `id` doesn't match
3. Call OTS API: `POST {url}/api/v1/share` with `secret=data`, auth via HTTP Basic (`api_user:api_key`). Extract `secret_key` from JSON response and build the link: `{url}/secret/{secret_key}`
4. Render Jinja2 template: `Environment(loader=FileSystemLoader(...))`, pass `name`, `secret_url`, `id`
5. Build `email.mime.multipart.MIMEMultipart('alternative')`, attach rendered HTML body
6. Send via `smtplib.SMTP(host, port)` with STARTTLS + login from config

#### Error handling
- Print a clear error and continue to next row on OTS API failure
- Abort on config parse failure or missing template

---

## Verification

1. `pip install -r requirements.txt`
2. Copy `config.ini.example` → `config.ini`, fill in real SMTP + OTS creds
3. Run against example CSV:
   ```
   python send.py --file example.csv --template templates/default.html.j2
   ```
4. Run with `--id` filter:
   ```
   python send.py --file example.csv --template templates/default.html.j2 --id 1
   ```
5. Confirm email received and OTS link works exactly once.
