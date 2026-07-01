from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    subdomain_prefix = models.CharField(max_length=100, unique=True)
    schema_name = models.CharField(max_length=63, unique=True, null=True, blank=True)

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="%(class)ss", null=True, blank=True)

    class Meta:
        abstract = True
