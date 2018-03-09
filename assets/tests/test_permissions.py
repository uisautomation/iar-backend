"""
Test custom DRF permissions

"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from assets import permissions
from assets.models import Asset, UserLookup

from . import clear_cached_person_for_user, set_cached_person_for_user


class OrPermissionTests(TestCase):

    def test_view_perms(self):
        """Test all combinations of two OR'd classes for the view permissions"""
        cases = (
            # 0 = A.has_permission(), 1 = B.has_permission(), 2 = expected result
            (False, False, False),
            (False, True, True),
            (True, False, True),
            (True, True, True),
        )
        for case in cases:
            class A(BasePermission):
                def has_permission(self, request, view):
                    return case[0]

            class B(BasePermission):
                def has_permission(self, request, view):
                    return case[1]
            self.assertEqual(permissions.OrPermission(A, B)().has_permission(None, None), case[2])

    def test_object_perms(self):
        """Test all combinations of two OR'd classes for the object permissions"""
        cases = (
            # 0 = A.has_permission(), 1 = A.has_object_permission(),
            # 2 = B.has_permission(), 3 = B.has_object_permission(),
            # 4 = expected result
            (False, False, False, False, False),
            (False, False, False, True, False),
            (False, False, True, False, False),
            (False, False, True, True, True),
            (False, True, False, False, False),
            (False, True, False, True, False),
            (False, True, True, False, False),
            (False, True, True, True, True),
            (True, False, False, False, False),
            (True, False, False, True, False),
            (True, False, True, False, False),
            (True, False, True, True, True),
            (True, True, False, False, True),
            (True, True, False, True, True),
            (True, True, True, False, True),
            (True, True, True, True, True),
        )
        for case in cases:
            class A(BasePermission):
                def has_permission(self, request, view):
                    return case[0]

                def has_object_permission(self, request, view, obj):
                    return case[1]

            class B(BasePermission):
                def has_permission(self, request, view):
                    return case[2]

                def has_object_permission(self, request, view, obj):
                    return case[3]

            perm = permissions.OrPermission(A, B)()
            self.assertEqual(
                perm.has_permission(None, None) and perm.has_object_permission(None, None, None),
                case[4]
            )


class AndPermissionTests(TestCase):

    def test_view_perms(self):
        """Test all combinations of two AND'd classes for the view permissions"""
        cases = (
            # 0 = A.has_permission(), 1 = B.has_permission(), 2 = expected result
            (False, False, False),
            (False, True, False),
            (True, False, False),
            (True, True, True),
        )
        for case in cases:
            class A(BasePermission):
                def has_permission(self, request, view):
                    return case[0]

            class B(BasePermission):
                def has_permission(self, request, view):
                    return case[1]
            self.assertEqual(permissions.AndPermission(A, B)().has_permission(None, None), case[2])

    def test_object_perms(self):
        """Test all combinations of two AND'd classes for the object permissions"""
        cases = (
            # 0 = A.has_permission(), 1 = B.has_permission(), 2 = expected result
            (False, False, False),
            (False, True, False),
            (True, False, False),
            (True, True, True),
        )
        for case in cases:
            class A(BasePermission):
                def has_object_permission(self, request, view, obj):
                    return case[0]

            class B(BasePermission):
                def has_object_permission(self, request, view, obj):
                    return case[1]
            self.assertEqual(
                permissions.AndPermission(A, B)().has_object_permission(None, None, None), case[2]
            )


class HasScopesPermissionTests(TestCase):
    def setUp(self):
        # Create a mock incoming request and view
        self.request = Request(HttpRequest())
        self.view = HasScopesPermissionTests.MockView()
        self.perm = permissions.HasScopesPermission()

    def test_requires_auth(self):
        """Request must have authentication information."""
        self.assertFalse(self.has_permission())

    def test_requires_dict_auth(self):
        """Request authorisation must be a dictionary."""
        self.request.auth = 'foo'
        self.assertFalse(self.has_permission())

    def test_requires_scopes(self):
        """Token must have required scopes."""
        self.request.auth = {'scope': 'SCOPEA SCOPEB'}
        self.assertTrue(self.has_permission())
        self.request.auth = {'scope': 'SCOPEA'}
        self.assertFalse(self.has_permission())
        self.request.auth = {'scope': 'SCOPEB'}
        self.assertFalse(self.has_permission())

    def test_extra_scopes(self):
        """Token may have extra scopes."""
        self.request.auth = {'scope': 'SCOPEA SCOPEB SCOPEC'}
        self.assertTrue(self.has_permission())

    def has_permission(self):
        """
        Convenience method to return the has_permission() method value when evaluated on the
        test's request and view instances.

        """
        return self.perm.has_permission(self.request, self.view)

    class MockView:
        """A mock view class which defines two required scopes."""
        required_scopes = ['SCOPEA', 'SCOPEB']


class UserInInstitutionPermissionTests(TestCase):

    def setUp(self):
        # Create a mock incoming request and view
        self.request = Request(HttpRequest())
        self.perm = permissions.UserInInstitutionPermission()

        # By default, authentication succeeds
        self.user = get_user_model().objects.create_user(username="test0001")
        self.user_lookup = UserLookup.objects.create(
            user=self.user, scheme='mock', identifier=self.user.username)
        self.request.user = self.user

        # Explicitly set the default user's lookup response
        set_cached_person_for_user(self.user, {'institutions': [{'instid': 'UIS'}]})

    def test_view_perms_true_for_all_except_POST(self):
        """check that the view permission returns true for all request methods expect POST"""
        for method in ('HEAD', 'OPTIONS', 'GET', 'PUT', 'PATCH', 'DELETE'):
            self.request.method = method
            self.assertTrue(self.has_permission())

    def test_view_perms_POST_department_not_set(self):
        """
        check the view permission raises an ValidationError when department is not part of a POST
        """
        self.request.method = 'POST'
        self.assertRaises(ValidationError, self.has_permission)

    def test_view_perms_POST_no_institution_in_cached_lookup(self):
        """check the view permission is false when the user's cached lookup has no institutions"""
        set_cached_person_for_user(self.user, {})
        self.request.method = 'POST'
        self.request.data['department'] = 'UIS'
        self.assertFalse(self.has_permission())

    def test_view_perms_POST_user_not_in_TESTDEPT(self):
        """check the view permission is false
        when the user's isn't associated with the asset's department"""
        set_cached_person_for_user(self.user, {'institutions': [{'instid': 'OTHER'}]})
        self.request.method = 'POST'
        self.request.data['department'] = 'UIS'
        self.assertFalse(self.has_permission())

    def test_view_perms_POST_true(self):
        """
        check the view permission is true when the user is associated with the asset's department
        """
        self.request.method = 'POST'
        self.request.data['department'] = 'UIS'
        self.assertTrue(self.has_permission())

    def test_object_perms_true_for_HEAD_OPTIONS_GET(self):
        """
        check that the object permission returns true for request methods HEAD, OPTIONS, and GET
        """
        for method in ('HEAD', 'OPTIONS', 'GET'):
            self.request.method = method
            self.assertTrue(self.has_object_permission(None))

    def test_object_perms_user_not_in_OTHER(self):
        """check that the object permission is false when
        the user isn't associated with the existing asset's department"""
        self.request.method = 'PATCH'
        self.request.data['department'] = 'UIS'
        self.assertFalse(self.has_object_permission(Asset(department='OTHER')))

    def test_object_perms_user_cant_change_to_OTHER(self):
        """check that the object permission is false when
        the user isn't associated with the asset's updated department"""
        self.request.method = 'PATCH'
        self.request.data['department'] = 'OTHER'
        self.assertFalse(self.has_object_permission(Asset(department='UIS')))

    def test_object_perms_user_can_change(self):
        """check that the object permission is true when
        the user is associated with the asset's existing and updated department"""
        self.request.method = 'PATCH'
        self.request.data['department'] = 'UIS'
        self.request.data['name'] = 'new name'
        self.assertTrue(self.has_object_permission(Asset(department='UIS')))

    def test_object_perms_user_can_delete(self):
        """check that the object permission is true when
        the user is associated with the asset's existing but no updated department is given"""
        self.request.method = 'DELETE'
        self.assertTrue(self.has_object_permission(Asset(department='UIS')))

    def has_permission(self):
        """convenience method to return the has_permission() method value
        when evaluated on the test's request"""
        return self.perm.has_permission(self.request, None)

    def has_object_permission(self, obj):
        """convenience method to return the has_object_permission() method value
        when evaluated on the test's request and object"""
        return (
            self.perm.has_permission(self.request, None) and
            self.perm.has_object_permission(self.request, None, obj)
        )

    def tearDown(self):
        clear_cached_person_for_user(self.user)


class UserInIARGroupPermissionTests(TestCase):

    def setUp(self):
        # Create a mock incoming request and view
        self.request = Request(HttpRequest())
        self.perm = permissions.UserInIARGroupPermission()

        # By default, authentication succeeds
        self.user = get_user_model().objects.create_user(username="test0001")
        UserLookup.objects.create(user=self.user, scheme='mock', identifier=self.user.username)
        self.request.user = self.user

    def test_no_cached_lookup(self):
        """check the view permission is false when there is not cached lookup for the user"""
        self.assertFalse(self.has_permission())

    def test_no_groups_in_cached_lookup(self):
        """check the view permission is false when the user's cached lookup has no groups"""
        set_cached_person_for_user(self.user, {})
        self.assertFalse(self.has_permission())

    def test_user_not_in_iar_group(self):
        """check the view permission is false
        when the user's isn't associated with the asset's department"""
        set_cached_person_for_user(self.user, {'groups': [{'name': 'other-group'}]})
        self.assertFalse(self.has_permission())

    def test_user_in_iar_group(self):
        """
        check the view permission is true when the user is associated with the asset's department
        """
        set_cached_person_for_user(self.user,
                                   {'groups': [{'name': settings.IAR_USERS_LOOKUP_GROUP}]})
        self.assertTrue(self.has_permission())

    def has_permission(self):
        """convenience method to return the has_permission() method value
        when evaluated on the test's request"""
        return self.perm.has_permission(self.request, None)

    def tearDown(self):
        clear_cached_person_for_user(self.user)
