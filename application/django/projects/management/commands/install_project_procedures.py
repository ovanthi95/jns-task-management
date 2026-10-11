"""Install version-controlled project stored procedures on the current database."""

import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Install one or more project stored procedures from the repository."

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+", help="SQL files relative to the repository root.")

    def handle(self, *args, **options):
        repository_root = Path(settings.BASE_DIR).parent.parent

        for relative_path in options["files"]:
            path = repository_root / relative_path

            if not path.is_file():
                raise CommandError(f"Stored procedure file not found: {relative_path}")

            self.stdout.write(f"Installing {relative_path}...")

            sql = path.read_text(encoding="utf-8")
            drop_match = re.search(
                r"DROP\s+PROCEDURE\s+IF\s+EXISTS\s+[^;]+;",
                sql,
                flags=re.IGNORECASE,
            )
            create_match = re.search(
                r"CREATE\s+PROCEDURE\s+.*?END\s*\$\$",
                sql,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if not drop_match or not create_match:
                raise CommandError(
                    f"Unsupported stored procedure format: {relative_path}"
                )

            create_sql = create_match.group(0)
            create_sql = re.sub(r"\$\$\s*$", "", create_sql).strip()

            with connection.cursor() as cursor:
                cursor.execute(drop_match.group(0))
                cursor.execute(create_sql)

            self.stdout.write(self.style.SUCCESS("  OK"))
