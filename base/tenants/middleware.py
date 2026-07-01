from django.db import connection
from django.http import Http404
from .models import Tenant

def hostname_from_request(request):

    return request.get_host().split(":")[0].lower()

class PureSchemaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host_name = hostname_from_request(request)
        subdomain_prefix = host_name.split(".")[0]

        if subdomain_prefix in ["localhost", "testapp", "www"]:
            schema_name = "public"

        else:
            tenant = Tenant.objects.filter(subdomain_prefix=subdomain_prefix).first()

            if tenant: 
                schema_name = tenant.schema_name
            else:
                raise Http404("Vendor workspace not found")
        
        with connection.cursor() as cursor:
            cursor.execute(f"SET  search_path TO {schema_name}, public")
        
        request.schema = schema_name

        print(f"{request.schema}")

        response = self.get_response(request)
        return response
