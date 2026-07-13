import gzip
import io
import os
import subprocess
from datetime import datetime, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Back up the database and email it. Always produces a human-readable "
        "dumpdata JSON (restorable with loaddata). Additionally attaches a full "
        "pg_dump SQL dump when pg_dump is available (restorable with psql)."
    )

    # Serializing these would only cause conflicts on restore — migrations
    # recreate content types and permissions, and sessions/log entries are
    # throwaway. Everything else (users, applicants, essays, activities,
    # colleges) is included.
    DUMPDATA_EXCLUDE = [
        "contenttypes",
        "auth.permission",
        "admin.logentry",
        "sessions.session",
    ]

    def handle(self, *args, **options):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")

        # 1. dumpdata JSON — the guaranteed floor. Pure Python, no external
        #    binary, so this cannot fail the way pg_dump has been failing.
        json_gz = self._dump_json()
        json_name = f"backup_{timestamp}.json.gz"
        self.stdout.write(f"dumpdata JSON: {len(json_gz) / 1024:.1f} KB compressed")

        attachments = [(json_name, json_gz)]

        # 2. pg_dump SQL — best-effort canonical dump for clean full restores.
        #    If the binary is missing or the version mismatches, we note it in
        #    the email and still ship the JSON rather than crashing.
        sql_gz, sql_error = self._dump_sql()
        sql_name = None
        if sql_gz is not None:
            sql_name = f"backup_{timestamp}.sql.gz"
            attachments.append((sql_name, sql_gz))
            self.stdout.write(f"pg_dump SQL: {len(sql_gz) / 1024:.1f} KB compressed")
        else:
            self.stderr.write(f"pg_dump unavailable — JSON only. Reason: {sql_error}")

        self._send_email(timestamp, attachments, json_name, sql_name, sql_error)
        self.stdout.write(self.style.SUCCESS(f"Backup emailed to {settings.BACKUP_EMAIL}"))

    def _dump_json(self):
        buf = io.StringIO()
        call_command(
            "dumpdata",
            natural_foreign=True,
            natural_primary=True,
            exclude=self.DUMPDATA_EXCLUDE,
            indent=2,
            stdout=buf,
        )
        return gzip.compress(buf.getvalue().encode("utf-8"))

    def _dump_sql(self):
        """Return (gzipped_sql, None) on success, or (None, error_message)."""
        # Use the public URL for pg_dump — the internal railway.internal
        # hostname is only reachable from within Railway's network.
        database_url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
        if not database_url:
            return None, "no DATABASE_PUBLIC_URL/DATABASE_URL set"

        try:
            result = subprocess.run(
                ["pg_dump", "--no-password", database_url],
                capture_output=True,
            )
        except FileNotFoundError:
            return None, "pg_dump binary not found in container"

        if result.returncode != 0:
            return None, result.stderr.decode(errors="replace").strip()

        return gzip.compress(result.stdout), None

    def _send_email(self, timestamp, attachments, json_name, sql_name, sql_error):
        import smtplib

        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_HOST_USER
        msg["To"] = settings.BACKUP_EMAIL
        msg["Subject"] = f"College App DB Backup — {timestamp[:10]}"

        body = [
            "Automated nightly backup from hippocampus.college.",
            "",
            f"Timestamp: {timestamp}",
            "",
            f"JSON ({json_name}) — human-readable, all app data.",
            "  Restore into a migrated, empty database with:",
            f"    python manage.py loaddata {json_name.removesuffix('.gz')}",
            "    (gunzip it first; then `python manage.py sqlsequencereset` on Postgres)",
            "",
        ]
        if sql_name:
            body += [
                f"SQL ({sql_name}) — full canonical pg_dump.",
                "  Restore into an empty database with:",
                f"    gunzip -c {sql_name} | psql <DATABASE_URL>",
            ]
        else:
            body += [
                "SQL dump: UNAVAILABLE this run.",
                f"  Reason: {sql_error}",
                "  (The JSON above is a complete backup — this is just the extra canonical copy.)",
            ]
        msg.attach(MIMEText("\n".join(body), "plain"))

        for name, data in attachments:
            attachment = MIMEApplication(data, Name=name)
            attachment["Content-Disposition"] = f'attachment; filename="{name}"'
            msg.attach(attachment)

        try:
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(msg)
        except Exception as exc:
            raise CommandError(f"Backup was generated but emailing failed: {exc}")
