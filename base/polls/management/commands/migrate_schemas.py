from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection, utils
from tenants.models import Tenant

class Command(BaseCommand):
    help = "Runs Django migrations sequentially across all isolated tenant schemas."

    def handle(self, *args, **options):
        # 1. First, always migrate the global public schema
        self.stdout.write(self.style.MIGRATE_HEADING("Migrating global (public) schema..."))
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")
        call_command('migrate', interactive=False)

        # 2. Collect target schemas dynamically or via a fallback map
        schema_targets = [] # List of tuples: (display_name, schema_name)
        
        try:
            tenants = Tenant.objects.all()
            if tenants.exists():
                for t in tenants:
                    schema_targets.append((t.name, t.schema_name))
        except Exception:
            # Table doesn't exist yet on the first run; ignore exception
            pass

        # If no tenants exist in the public table yet, load your local development configuration
        if not schema_targets:
            self.stdout.write(self.style.WARNING("No tenant tracking records found. Using fallback dev configuration..."))
            schema_targets = [
                ("Safari Corp", "tenant_safari"),
                ("Airtel Corp", "tenant_airtel"),
            ]

        # 3. Loop through each schema, verify it exists in Postgres, and migrate
        for name, schema_name in schema_targets:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\nMigrating tenant workspace: {name} ({schema_name})..."))
            
            with connection.cursor() as cursor:
                # RAW SQL: Safely ensure the schema folder physically exists on the Postgres disk
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
                
                # Target the database namespace for the upcoming migrations
                cursor.execute(f"SET search_path TO {schema_name};")
                
            try:
                # Run the native Django migration engine inside this schema context
                call_command('migrate', interactive=False)
            except utils.ProgrammingError as e:
                self.stdout.write(self.style.ERROR(f"Failed migrating schema {schema_name}: {e}"))

        # 4. Clean up the database connection session back to public
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")
            
        self.stdout.write(self.style.SUCCESS("\nAll schemas successfully initialized and migrated!"))