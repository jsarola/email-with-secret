import argparse
import configparser
import csv
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


def load_config(path: str) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if not cfg.read(path):
        sys.exit(f"Config file not found: {path}")
    for section in ("smtp", "onetimesecret"):
        if section not in cfg:
            sys.exit(f"Missing [{section}] section in {path}")
    return cfg


def create_secret(ots_url: str, api_user: str, api_key: str, data: str) -> str:
    endpoint = f"{ots_url.rstrip('/')}/api/v1/share"
    try:
        resp = requests.post(
            endpoint,
            data={"secret": data},
            auth=(api_user, api_key),
            timeout=15,
        )
        resp.raise_for_status()
        secret_key = resp.json()["secret_key"]
        return f"{ots_url.rstrip('/')}/secret/{secret_key}"
    except (requests.RequestException, KeyError) as exc:
        raise RuntimeError(f"OTS API error: {exc}") from exc


def send_email(cfg: configparser.ConfigParser, to: str, subject: str, html_body: str) -> None:
    smtp_cfg = cfg["smtp"]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_cfg["from"]
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    host = smtp_cfg["host"]
    port = smtp_cfg.getint("port", 587)
    use_tls = smtp_cfg.getboolean("use_tls", True)

    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls()
        server.login(smtp_cfg["username"], smtp_cfg["password"])
        server.sendmail(smtp_cfg["from"], to, msg.as_string())


def load_template(template_path: str):
    path = Path(template_path)
    env = Environment(loader=FileSystemLoader(str(path.parent)), autoescape=True)
    try:
        return env.get_template(path.name)
    except TemplateNotFound:
        sys.exit(f"Template not found: {template_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send personalised secrets via email.")
    parser.add_argument("--file", required=True, help="Path to semicolon-delimited CSV (id;name;data;email)")
    parser.add_argument("--template", required=True, help="Path to Jinja2 email template")
    parser.add_argument("--id", dest="filter_id", default=None, help="Only process rows with this id")
    parser.add_argument("--config", default="config.ini", help="Path to config file (default: config.ini)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    template = load_template(args.template)

    ots = cfg["onetimesecret"]
    ots_url = ots["url"]
    api_user = ots["api_user"]
    api_key = ots["api_key"]

    try:
        csv_file = open(args.file, newline="", encoding="utf-8")
    except OSError as exc:
        sys.exit(f"Cannot open CSV: {exc}")

    with csv_file:
        reader = csv.reader(csv_file, delimiter=";")
        for row in reader:
            if len(row) < 4:
                print(f"Skipping malformed row: {row}")
                continue

            row_id, name, data, email = row[0], row[1], row[2], row[3]

            if args.filter_id and row_id != args.filter_id:
                continue

            print(f"[{row_id}] Processing {email} ...")

            try:
                secret_url = create_secret(ots_url, api_user, api_key, data)
            except RuntimeError as exc:
                print(f"[{row_id}] ERROR: {exc} — skipping.")
                continue

            html_body = template.render(id=row_id, name=name, secret_url=secret_url)

            try:
                send_email(cfg, email, f"Your secure link", html_body)
                print(f"[{row_id}] Sent to {email}")
            except smtplib.SMTPException as exc:
                print(f"[{row_id}] SMTP error: {exc} — skipping.")


if __name__ == "__main__":
    main()
