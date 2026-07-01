from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from tenants.models import Tenant
from polls.models import Poll, Choice
from faker import Faker
import random

class Command(BaseCommand):
    help = "Seeds the database with master tenant routing entries and isolated poll data."

    def handle(self, *args, **kwargs):
        fake = Faker()

        self.stdout.write("Clearing global router data...")
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")
        Tenant.objects.all().delete()

        self.stdout.write("Creating Tenant Router Records in public schema...")
        tenant_configs = [
            {"prefix": "tenant1", "schema": "tenant_safari", "name": "Safari Corp"},
            {"prefix": "tenant2", "schema": "tenant_airtel", "name": "Airtel Corp"},
        ]
        
        for config in tenant_configs:
            # --- FORCE PUBLIC RESET ---
            # Ensure the connection is always in public before trying to touch the router table!
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public;")

            tenant = Tenant.objects.create(
                name=config["name"],
                subdomain_prefix=config["prefix"],
                schema_name=config["schema"]
            )
            self.stdout.write(f"  -> Created Routing Entity: {tenant.name} -> Schema: {tenant.schema_name}")

            # --- SWITCH CONTEXT FOR ISOLATED DATA ---
            self.stdout.write(f"  Populating isolated data for {tenant.name}...")
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {config['schema']};")

            # Wipe old schema data inside this isolated workspace room
            Choice.objects.all().delete()
            Poll.objects.all().delete()
            User.objects.all().delete()

            # Create an isolated tenant user inside THIS specific schema table
            tenant_user = User.objects.create_user(
                username="admin",
                password="admin123",
                is_staff=True,
                is_superuser=True
            )

            # Create 3 unique polls linked to the user inside this exact same schema folder
            for _ in range(3):
                poll = Poll.objects.create(
                    question=fake.sentence(nb_words=6).replace(".", "?"),
                    created_by=tenant_user
                )
                
                for _ in range(random.randint(3, 5)):
                    Choice.objects.create(
                        poll=poll,
                        choice_text=fake.word().capitalize()
                    )
                    
            self.stdout.write(f"  Successfully seeded isolated tables for {tenant.name}!")

        # Reset session back to public
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")

        self.stdout.write(self.style.SUCCESS("Database schema seeding complete!"))