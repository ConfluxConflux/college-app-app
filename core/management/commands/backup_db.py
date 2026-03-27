import gzip
import os
import subprocess
from datetime import datetime, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "pg_dump the production database and email it as a gzipped attachment."

    def handle(self, *args, **options):
        # Use public URL for pg_dump — the internal railway.internal hostname
        # is only reachable from within Railway's network.
        database_url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
        if not database_url:
            raise CommandError("DATABASE_URL is not set — nothing to back up.")

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        filename = f"backup_{timestamp}.sql.gz"

        self.stdout.write(f"Running pg_dump → {filename} …")

        result = subprocess.run(
            ["pg_dump", "--no-password", database_url],
            capture_output=True,
        )
        if result.returncode != 0:
            raise CommandError(f"pg_dump failed:\n{result.stderr.decode()}")

        compressed = gzip.compress(result.stdout)
        self.stdout.write(f"Dump size: {len(compressed) / 1024:.1f} KB compressed")

        self._send_email(filename, compressed, timestamp)
        self.stdout.write(self.style.SUCCESS(f"Backup emailed to {settings.BACKUP_EMAIL}"))

    def _send_email(self, filename, data, timestamp):
        import smtplib

        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_HOST_USER
        msg["To"] = settings.BACKUP_EMAIL
        msg["Subject"] = f"College App DB Backup — {timestamp[:10]}"

        msg.attach(MIMEText(
            f"Automated nightly backup from collegeappapp.com.\n\n"
            f"Timestamp: {timestamp}\n"
            f"Compressed size: {len(data) / 1024:.1f} KB\n\n"
            f"Restore with:\n"
            f"  gunzip -c {filename} | psql <DATABASE_URL>",
            "plain",
        ))

        attachment = MIMEApplication(data, Name=filename)
        attachment["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(attachment)

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)
