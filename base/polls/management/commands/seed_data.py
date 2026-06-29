from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tenants.models import Tenant
from polls.models import Poll, Choice
from faker import Faker
import random

class Command(BaseCommand):
    help = "Seeds the database with test tenants and poll data."

    def handle(self, *args, **kwargs):
        fake = Faker()

        self.stdout.write("Clearing old data...")
        Choice.objects.all().delete()
        Poll.objects.all().delete()
        Tenant.objects.all().delete()
        
        # Ensure we have at least one superuser/user to assign as creator
        user, _ = User.objects.get_or_create(
            username="admin", 
            defaults={"is_staff": True, "is_superuser": True}
        )
        user.set_password("admin123")
        user.save()

        self.stdout.write("Creating Tenants...")
        # We will explicitly create prefixes matching your /etc/hosts setup!
        tenant_prefixes = ["tenant1", "tenant2"]
        tenants = []
        
        for prefix in tenant_prefixes:
            tenant = Tenant.objects.create(
                name=f"{prefix.capitalize()} Corp",
                subdomain_prefix=prefix
            )
            tenants.append(tenant)
            self.stdout.write(f"  -> Created Tenant: {tenant.name} ({prefix}.testapp.local)")

        self.stdout.write("Populating Polls and Choices...")
        for tenant in tenants:
            # Create 3 unique polls per tenant
            for _ in range(3):
                poll = Poll.objects.create(
                    tenant=tenant,
                    question=fake.sentence(nb_words=6).replace(".", "?"),
                    created_by=user
                )
                
                # Create 3 to 5 choices for this specific poll
                for _ in range(random.randint(3, 5)):
                    Choice.objects.create(
                        tenant=tenant, # Keeps data aligned under the same tenant
                        poll=poll,
                        choice_text=fake.word().capitalize()
                    )
                    
            self.stdout.write(f"  Successfully seeded data for {tenant.name}!")

        self.stdout.write(self.style.SUCCESS("Database seeding complete!"))