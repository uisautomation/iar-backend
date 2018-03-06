"""
OAuth2 token-based permissions for Django REST Framework views.

"""
import logging

from django.core.cache import cache
from rest_framework import permissions
from rest_framework.exceptions import ValidationError

LOG = logging.getLogger(__name__)


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


class UserInInstitutionPermission(permissions.BasePermission):
    """
    Django REST framework permission which requires that the user acting on an asset be associated
    with the department that the asset belongs to.
    """
    def has_permission(self, request, view):
        """
        When a new asset is created check that the user is associated with the given department.
        """

        # PUT, PATCH, and DELETE should return true here
        # otherwise has_object_permission() will never be called.
        if request.method != 'POST':
            return True

        department = request.data.get('department')
        if not department:
            raise ValidationError('department is required')

        return self._validate_asset_user_institution(request.user, department)

    def has_object_permission(self, request, view, obj):
        """
        When a new asset is changed/deleted
        check that the user is associated with the department of the existing asset
        AND (in the case of changed) is also associated with the given department.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        if not self._validate_asset_user_institution(request.user, obj.department):
            return False
        # in the case of PATCH, department may not have have been given
        if 'department' in request.data and not \
                self._validate_asset_user_institution(request.user, request.data['department']):
            return False
        return True

    @staticmethod
    def _validate_asset_user_institution(user, department):
        """Validates that the user is member of the department that the asset belongs to
        (asset_department)."""

        lookup_response = cache.get("{user.username}:lookup".format(user=user))
        if lookup_response is None:
            LOG.error('No cached lookup response for user %s', user.username)
            return False

        institutions = lookup_response.get('institutions')
        if institutions is None:
            LOG.error('No institutions in cached lookup response for user %s', user.username)
            return False

        for institution in lookup_response.get('institutions', []):
            if department == institution['instid']:
                return True

        return False


def OrPermission(*args):
    """
    This is a function posing as a class. An example of it's intended usage is

    ..code::
        permission_classes = (OrPermission(A, B), )

    where A & B are both class that extend from BasePermission. The function returns a class that,
    when instantiated authorise a request when either A or B authorise that request.

    :param args: a tuple of BasePermission subclasses
    :return: an OrPermissionClass closure
    """
    class OrPermissionClass(permissions.BasePermission):

        def __init__(self):
            # instantiate each permission class
            self.permissions = [Permission() for Permission in args]
            # check that all given permissions inherit from BasePermission
            for permission in self.permissions:
                assert issubclass(type(permission), permissions.BasePermission)

        def has_permission(self, request, view):
            """is true when has_permission() for any of the permissions is true"""
            for permission in self.permissions:
                if permission.has_permission(request, view):
                    return True
            return False

        def has_object_permission(self, request, view, obj):
            """This is true when BOTH has_permission() AND has_object_permission()
            for any of the permissions is true.
            This is important because of the case where X.has_permission() returns false
            but X.has_object_permission() has been left unimplemented and thus returns true.
            This in combination with Y.has_permission() = true and
            Y.has_object_permission() = false would otherwise return true incorrectly.
            """
            for permission in self.permissions:
                if permission.has_permission(request, view) \
                        and permission.has_object_permission(request, view, obj):
                    return True
            return False

    return OrPermissionClass
