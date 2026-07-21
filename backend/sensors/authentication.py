"""
Machine-to-machine authentication for the fog ingestion endpoint.

Fog nodes are not users -- they never log in and don't hold a JWT. They
authenticate with a static shared secret sent as a header, which is the
simplest form of device authentication and is enough to satisfy "the
ingestion endpoint isn't wide open" for this project. A production
system would use per-device credentials/certificates (e.g. AWS IoT Core
mutual TLS) instead of one shared key -- worth a line in the report's
"future work" section.
"""
from django.conf import settings
from rest_framework import authentication, exceptions


class FogNodeAPIKeyAuthentication(authentication.BaseAuthentication):
    keyword = "X-API-Key"

    def authenticate(self, request):
        provided_key = request.headers.get("X-API-Key")

        if not provided_key:
            # Returning None (not raising) lets DRF fall through to
            # "unauthenticated", which the view's permission_classes then
            # rejects with a clean 401/403 instead of a 500.
            return None

        if provided_key != settings.FOG_INGEST_API_KEY:
            raise exceptions.AuthenticationFailed("Invalid fog node API key.")

        # DRF authenticate() must return a (user, auth) tuple. There's no
        # Django user for a device, so we return None for the user and the
        # key itself as the "auth" object.
        return (None, provided_key)
