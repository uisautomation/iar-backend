"""
OAuth2 token-based permissions for Django REST Framework views.

"""
import logging

from django.core.cache import cache
from rest_framework import permissions


LOG = logging.getLogger()


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


def validate_asset_user_institution(user=None, department=None):
    """Validates that the user is member of the department that the asset belongs to
    (asset_department). raises PermissionDenied if it doesn't, passes otherwise."""

    if user is None or department is None:
        return False

    lookup_response = cache.get("{user.username}:lookup".format(user=user))
    if lookup_response is None:
        LOG.error('No cached lookup response for user %s', user.username)
        return False

    institutions = lookup_response.get('institutions')
    if institutions is None:
        LOG.error('No institutions in cached lookup response for user %s', user.username)
        return False

    institutions = map(lambda inst: inst['instid'],
                       lookup_response.get('institutions', []))
    if department not in institutions:
        return False

    return True


class UserInInstitutionPermission(permissions.BasePermission):
    """

    """
    def has_permission(self, request, view):
        """
        POST
        :param request:
        :param view:
        :return:
        """

        # ????
        if request.method != 'POST':
            return True

        assert 'department' in request.data, "the department is required"

        # Check permissions for write request
        return validate_asset_user_institution(request.user, request.data['department'])

    def has_object_permission(self, request, view, obj):
        """
        PUT PATCH DELETE
        :param request:
        :param view:
        :param obj:
        :return:
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        if not validate_asset_user_institution(request.user, obj.department):
            return False
        if 'department' in request.data and \
                not validate_asset_user_institution(request.user, request.data['department']):
            return False
        return True


def OrPermission(*args):
    """
    FIXME
    :param args:
    :return:
    """
    class OrPermissionClass(permissions.BasePermission):

        def __init__(self):
            self.permissions = [Permission() for Permission in args]
            # check that all given permissions inherit from BasePermission
            for permission in self.permissions:
                assert issubclass(type(permission), permissions.BasePermission)

        def has_permission(self, request, view):
            """
            """
            for permission in self.permissions:
                if permission.has_permission(request, view):
                    return True
            return False

        def has_object_permission(self, request, view, obj):
            """
            """
            for permission in self.permissions:
                if permission.has_permission(request, view) \
                        and permission.has_object_permission(request, view, obj):
                    return True
            return False

    return OrPermissionClass
