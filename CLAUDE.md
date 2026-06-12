# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python CLI that reads a semicolon-delimited CSV (`id;name;data;email`), creates a [OneTimeSecret](https://onetimesecret.com) link for each row's `data` field, renders a Jinja2 HTML email template, and sends it via SMTP.

## Setup

```bash
# pip
pip install -r requirements.txt

# Poetry (preferred)
poetry config virtualenvs.in-project true   # keeps .venv inside the project
poetry install
poetry shell
```

```bash
cp config.ini.example config.ini   # then fill in real credentials
```

## Running

```bash
# Send to all rows
python send.py --file example.csv --template templates/default.html.j2

# Send only to row with id=1
python send.py --file example.csv --template templates/default.html.j2 --id 1

# Without activating the Poetry shell
poetry run python send.py --file example.csv --template templates/default.html.j2
```

## Architecture

- `send.py` — single entry point; all logic lives here (arg parsing, CSV reading, OTS API call, template rendering, SMTP send).
- `config.ini` — INI file with `[smtp]` (host, port, username, password, from, use_tls) and `[onetimesecret]` (url, api_user, api_key) sections. Not committed; use `config.ini.example` as the template.
- `templates/` — Jinja2 `.html.j2` files. Templates receive `id`, `name`, `secret_url` variables.
- CSV format: no header row, fields `id;name;data;email`.

## OneTimeSecret API

Endpoint: `POST {url}/api/v1/share` with form field `secret=<data>` and HTTP Basic auth (`api_user:api_key`). The `url` in config supports both `https://onetimesecret.com` and self-hosted instances (e.g. `https://secret.example.com`).
