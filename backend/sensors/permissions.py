from rest_framework import permissions


class IsAuthenticatedFogNode(permissions.BasePermission):
    """
    Passes only when FogNodeAPIKeyAuthentication successfully authenticated
    the request (i.e. request.auth holds the validated API key). There is
    no Django User for a fog node, so the default IsAuthenticated check
    (which looks at request.user) doesn't apply here.
    """

    def has_permission(self, request, view):
        return bool(getattr(request, "auth", None))
