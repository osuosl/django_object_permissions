from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase

from object_permissions.backend import ObjectPermBackend
from object_permissions.models import UserGroup
from object_permissions import register


class TestBackend(TestCase):

    def setUp(self):
        self.tearDown()
        settings.ANONYMOUS_USER_ID = 0
        user = User(id=1, username="tester")
        user.save()
        register('Permission', UserGroup)
        object_ = UserGroup(name='testing')
        object_.save()
        user.grant('Permission', object_)
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
        self.assertFalse(anonymous.has_perm('Permission', object_))
        self.assert_(user.has_perm('Permission', object_))
    
    def test_anonymous_user_does_not_exist(self):
        """
        Tests to ensure that anonymous user is auto created if it does not
        already exist
        """
        backend = ObjectPermBackend()
        self.assertFalse(anonymous.has_perm('Permission', object_))
        self.assert_(backend.has_perm(user, 'Permission', object_))