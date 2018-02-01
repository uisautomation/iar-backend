"""
OAuth2 token-based permissions for Django REST Framework views.

"""
from rest_framework import permissions


class HasScopesPermission(permissions.BasePermission):
    """
    Django REST framework permission which requires that the scopes granted to an OAuth2 token are
    a superset of those required for the view. The requires scopes are specified by the
    :py:attr:`required_scopes` attribute of the view class.

    """
    def has_permission(self, request, view):
        token = request.auth

        # If there is not token, or if it isn't a dictionary, the request is definitely not
        # allowed.
        if not isinstance(token, dict):
            return False

        granted_scopes = set(token.get('scope', '').split(' '))
        required_scopes = set(getattr(view, 'required_scopes', []))

        return required_scopes <= granted_scopes
