# email-with-secret

A Python CLI tool that reads recipient data from a CSV file, generates a [OneTimeSecret](https://onetimesecret.com) link for each recipient's secret data, and sends a personalised HTML email via SMTP.

Useful for securely distributing passwords, tokens, or any one-time sensitive information to a list of people.

---

## How it works

1. Reads a semicolon-delimited CSV file (`id;name;data;email`)
2. For each row, calls the OneTimeSecret API to create a single-use secret link from the `data` field
3. Renders a Jinja2 HTML email template with the recipient's name and the generated link
4. Sends the email via SMTP (with STARTTLS support)

---

## Requirements

- Python 3.8+

---

## Installation

### Option A — pip

```bash
pip install -r requirements.txt
```

### Option B — Poetry (recommended)

[Poetry](https://python-poetry.org/) manages the virtual environment and dependencies for you.

**1. Install Poetry** (if not already installed):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**2. Create the virtual environment and install dependencies:**

```bash
poetry install
```

Poetry creates a `.venv` folder inside the project directory (or in its cache, depending on your config). To keep it local to the project:

```bash
poetry config virtualenvs.in-project true  # run once, applies globally
poetry install
```

**3. Activate the virtual environment:**

```bash
poetry shell
```

Once inside the shell, run the script normally:

```bash
python send.py --file example.csv --template templates/default.html.j2
```

Or run without activating the shell:

```bash
poetry run python send.py --file example.csv --template templates/default.html.j2
```

**4. Add or remove dependencies:**

```bash
poetry add <package>
poetry remove <package>
```

---

## Configuration

Copy the example config and fill in your credentials:

```bash
cp config.ini.example config.ini
```

`config.ini` structure:

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

- `url` under `[onetimesecret]` accepts both the public service (`https://onetimesecret.com`) and self-hosted instances (e.g. `https://secret.example.com`).
- `config.ini` is not committed to version control. Only `config.ini.example` (with placeholder values) is.

---

## CSV format

No header row. Fields separated by semicolons:

```
id;name;data;email
```

Example (`example.csv`):

```
1;John Ripper;123456789;john.ripper@mail.com
```

| Field | Description |
|-------|-------------|
| `id` | Unique identifier for the row |
| `name` | Recipient's display name (used in the template) |
| `data` | The secret to be stored in OneTimeSecret |
| `email` | Recipient's email address |

---

## Email templates

Templates are Jinja2 HTML files (`.html.j2`) stored in the `templates/` directory. The following variables are available inside every template:

| Variable | Description |
|----------|-------------|
| `{{ name }}` | Recipient's name |
| `{{ secret_url }}` | The generated OneTimeSecret link |
| `{{ id }}` | Row id from the CSV |

A default template is provided at `templates/default.html.j2`.

---

## Usage

```bash
# Send to all rows in the CSV
python send.py --file example.csv --template templates/default.html.j2

# Send only to the row with id=1
python send.py --file example.csv --template templates/default.html.j2 --id 1

# Use a custom config file
python send.py --file example.csv --template templates/default.html.j2 --config /path/to/config.ini
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--file` | Yes | — | Path to the CSV file |
| `--template` | Yes | — | Path to the Jinja2 template |
| `--id` | No | — | Only process the row with this id |
| `--config` | No | `config.ini` | Path to the config file |

---

## Project structure

```
email-with-secret/
├── send.py               # Main script
├── config.ini            # Your local config (not committed)
├── config.ini.example    # Config template (safe to commit)
├── example.csv           # Sample CSV with one row
├── pyproject.toml        # Poetry project definition
├── requirements.txt      # pip dependencies (alternative to Poetry)
├── .venv/                # Virtual environment created by Poetry (not committed)
├── .gitignore
└── templates/
    └── default.html.j2   # Default email template
```

---

## OneTimeSecret API

The tool uses the [OneTimeSecret REST API](https://docs.onetimesecret.com/):

- **Endpoint:** `POST {url}/api/v1/share`
- **Auth:** HTTP Basic (`api_user:api_key`)
- **Payload:** form field `secret=<data>`
- **Response:** JSON with `secret_key`; final link is `{url}/secret/{secret_key}`

The link can only be opened once — after that it is permanently destroyed.
