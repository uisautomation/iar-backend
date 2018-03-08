import unittest.mock as mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from assets import lookup, models

from . import clear_cached_person_for_user


class LookupTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test0001')
        self.user_lookup = models.UserLookup.objects.create(
            user=self.user, scheme='mock', identifier=self.user.username)
        self.anonymous_user = AnonymousUser()

        # Ensure the Django cache is "clean" between calls.
        clear_cached_person_for_user(self.user)

    def test_anonymous_user(self):
        """Calling get_person_for_user with the anonymous user fails."""
        with self.assertRaises(lookup.LookupError):
            lookup.get_person_for_user(self.anonymous_user)

    def test_no_lookup_user(self):
        """Calling get_person_for_user with a Django user with no corresponding lookup user
        fails.

        """
        self.user_lookup.delete()
        with self.assertRaises(lookup.LookupError):
            lookup.get_person_for_user(self.user)

    def test_simple_call(self):
        """A simple call to get_person_for_user succeeds."""
        mock_response = {
            'url': 'http://lookupproxy.invalid/people/xxx',
            'institutions': [{'instid': 'INSTA'}, {'instid': 'INSTB'}],
        }

        with self.mocked_session() as LOOKUP_SESSION:
            LOOKUP_SESSION.request.return_value.json.return_value = mock_response
            response = lookup.get_person_for_user(self.user)

        self.assertEqual(response, mock_response)
        LOOKUP_SESSION.request.assert_called_once_with(
            url='http://lookupproxy.invalid/people/mock/test0001?fetch=all_insts,all_groups',
            method='GET'
        )

    def test_results_are_cached(self):
        """Two calls to get_person_for_user succeeds only results in one lookup API call."""
        mock_response = {
            'url': 'http://lookupproxy.invalid/people/xxx',
            'institutions': [{'instid': 'INSTA'}, {'instid': 'INSTB'}],
        }

        with self.mocked_session() as LOOKUP_SESSION:
            LOOKUP_SESSION.request.return_value.json.return_value = mock_response
            lookup.get_person_for_user(self.user)
            lookup.get_person_for_user(self.user)

        LOOKUP_SESSION.request.assert_called_once_with(
            url='http://lookupproxy.invalid/people/mock/test0001?fetch=all_insts,all_groups',
            method='GET'
        )

    def mocked_session(self):
        """Return a patch for the assets.lookup.LOOKUP_SESSION object."""
        return mock.patch('assets.lookup.LOOKUP_SESSION')
