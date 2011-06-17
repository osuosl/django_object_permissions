from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser, Group
from django.test import TestCase

from object_permissions.backend import ObjectPermBackend

global user, anonymous, object_


class TestBackend(TestCase):

    def setUp(self):
        self.tearDown()
        settings.ANONYMOUS_USER_ID = 0
        user = User(id=1, username="tester")
        user.save()
        object_ = Group(name='testing')
        object_.save()
        user.grant('admin', object_)
        g = globals()
        g['anonymous'] = AnonymousUser()
        g['user'] = user
        g['object_'] = object_

    def tearDown(self):
        User.objects.all().delete()
        settings.ANONYMOUS_USER_ID = 0

    def test_trivial(self):
        ObjectPermBackend()

    def test_no_anonymous_user_setting(self):
        """
        Tests the backend when there is no anonymous user setting
        """
        del settings.ANONYMOUS_USER_ID
        self.assertFalse(hasattr(settings, 'ANONYMOUS_USER_ID'))
        backend = ObjectPermBackend()
        self.assertFalse(anonymous.has_perm('admin', object_))
        self.assert_(user.has_perm('admin', object_))

    def test_anonymous_user_does_not_exist(self):
        """
        Tests to ensure that anonymous user is auto created if it does not
        already exist
        """
        backend = ObjectPermBackend()
        self.assertFalse(anonymous.has_perm('admin', object_))
        self.assert_(backend.has_perm(user, 'admin', object_))

    def test_has_perm(self):
        """
        Verify that has_perm() works as desired.
        """

        backend = ObjectPermBackend()
        self.assertTrue(user.has_perm("admin", object_))
        self.assertTrue(backend.has_perm(user, "admin", object_))

    def test_get_all_permissions(self):
        """
        Verify that get_all_permissions() works as desired.

        This test is quirked due to Django #14764.
        """

        backend = ObjectPermBackend()
        permissions = ["admin"]
        # Quirky; see Django #14764.
        self.assertEqual(permissions, list(user.get_all_permissions(object_)))
        self.assertEqual(permissions, backend.get_all_permissions(user,
            object_))
