
from django.contrib.auth.models import User
from django.test import TestCase

from object_permissions import register, grant, revoke, get_user_perms, \
    revoke_all, get_users, set_user_perms
from object_permissions.registration import TestModel, UnknownPermissionException


class TestModelPermissions(TestCase):
    perms = [u'Perm1', u'Perm2', u'Perm3', u'Perm4']

    def setUp(self):
        self.tearDown()
        self.user0 = User(id=2, username='tester')
        self.user0.save()
        self.user1 = User(id=3, username='tester2')
        self.user1.save()
        
        self.object0 = TestModel.objects.create(name='test0')
        self.object0.save()
        self.object1 = TestModel.objects.create(name='test1')
        self.object1.save()
        
        dict_ = globals()
        dict_['user0']=self.user0
        dict_['user1']=self.user1
        dict_['object0']=self.object0
        dict_['object1']=self.object1
        dict_['perms']=self.perms

    def tearDown(self):
        TestModel.objects.all().delete()
        User.objects.all().delete()

    def test_trivial(self):
        pass

    def test_grant_user_permissions(self):
        """
        Grant a user permissions
        
        Verifies:
            * granted properties are available via backend (has_perm)
            * granted properties are only granted to the specified user, object
              combinations
            * granting unknown permission raises error
        """
        # grant single property
        grant(user0, 'Perm1', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        
        # grant property again
        grant(user0, 'Perm1', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        
        # grant second property
        grant(user0, 'Perm2', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        self.assert_(user0.has_perm('Perm2', object0))
        self.assertFalse(user0.has_perm('Perm2', object1))
        self.assertFalse(user1.has_perm('Perm2', object0))
        self.assertFalse(user1.has_perm('Perm2', object1))
        
        # grant property to another object
        grant(user0, 'Perm2', object1)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        self.assert_(user0.has_perm('Perm2', object0))
        self.assert_(user0.has_perm('Perm2', object1))
        self.assertFalse(user1.has_perm('Perm2', object0))
        self.assertFalse(user1.has_perm('Perm2', object1))
        
        # grant perms to other user
        grant(user1, 'Perm3', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        self.assert_(user0.has_perm('Perm2', object0))
        self.assert_(user0.has_perm('Perm2', object1))
        self.assertFalse(user1.has_perm('Perm2', object0))
        self.assertFalse(user1.has_perm('Perm2', object1))
        self.assert_(user1.has_perm('Perm3', object0))
        
        def grant_unknown():
            grant(user1, 'UnknownPerm', object0)
        self.assertRaises(UnknownPermissionException, grant_unknown)
    
    def test_revoke_user_permissions(self):
        """
        Test revoking permissions from users
        
        Verifies:
            * revoked properties are removed
            * revoked properties are only removed from the correct user/obj combinations
            * revoking property user does not have does not give an error
            * revoking unknown permission raises error
        """
        
        # revoke perm when user has no perms
        revoke(user0, 'Perm1', object0)
        
        for perm in perms:
            grant(user0, perm, object0)
            grant(user0, perm, object1)
            grant(user1, perm, object0)
            grant(user1, perm, object1)
        
        # revoke single perm
        revoke(user0, 'Perm1', object0)
        self.assertEqual([u'Perm2', u'Perm3', u'Perm4'], get_user_perms(user0, object0))
        self.assertEqual(perms, get_user_perms(user0, object1))
        self.assertEqual(perms, get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
        
        # revoke a second perm
        revoke(user0, 'Perm3', object0)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(user0, object0))
        self.assertEqual(perms, get_user_perms(user0, object1))
        self.assertEqual(perms, get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
        
        # revoke from another object
        revoke(user0, 'Perm3', object1)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(user0, object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], get_user_perms(user0, object1))
        self.assertEqual(perms, get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
        
        # revoke from another user
        revoke(user1, 'Perm4', object0)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(user0, object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], get_user_perms(user0, object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
        
        # revoke perm user does not have
        revoke(user0, 'Perm1', object0)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(user0, object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], get_user_perms(user0, object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
        
        # revoke perm that does not exist
        revoke(user0, 'DoesNotExist', object0)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(user0, object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], get_user_perms(user0, object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
    
    def test_revoke_all(self):
        """
        Test revoking all permissions from a user
        
        Verifies
            * revoked properties are only removed from the correct user/obj combinations
            * revoking property user does not have does not give an error
            * revoking unknown permission raises error
        """
        for perm in perms:
            grant(user0, perm, object0)
            grant(user0, perm, object1)
            grant(user1, perm, object0)
            grant(user1, perm, object1)
        
        revoke_all(user0, object0)
        self.assertEqual([], get_user_perms(user0, object0))
        self.assertEqual(perms, get_user_perms(user0, object1))
        self.assertEqual(perms, get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
        
        revoke_all(user0, object1)
        self.assertEqual([], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual(perms, get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
        
        revoke_all(user1, object0)
        self.assertEqual([], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual(perms, get_user_perms(user1, object1))
        
        revoke_all(user1, object1)
        self.assertEqual([], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
    
    def test_set_perms(self):
        """
        Test setting perms to an exact set
        """
        user0 = self.user0
        user1 = self.user1
        object0 = self.object0
        object1 = self.object1
        
        perms1 = self.perms
        perms2 = ['Perm1', 'Perm2']
        perms3 = ['Perm2', 'Perm3']
        perms4 = []

        # grant single property
        set_user_perms(user0, perms1, object0)
        self.assertEqual(perms1, get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user0, perms2, object0)
        self.assertEqual(perms2, get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user0, perms3, object0)
        self.assertEqual(perms3, get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user0, perms4, object0)
        self.assertEqual(perms4, get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user0, perms2, object1)
        self.assertEqual(perms4, get_user_perms(user0, object0))
        self.assertEqual(perms2, get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user1, perms1, object0)
        self.assertEqual(perms4, get_user_perms(user0, object0))
        self.assertEqual(perms2, get_user_perms(user0, object1))
        self.assertEqual(perms1, get_user_perms(user1, object0))
    
    def test_has_perm(self):
        """
        Additional tests for has_perms
        
        Verifies:
            * None object always returns false
            * Nonexistent perm returns false
            * Perm user does not possess returns false
        """
        grant(user0, 'Perm1', object0)
        
        self.assertTrue(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', None))
        self.assertFalse(user0.has_perm('DoesNotExist'), object0)
        self.assertFalse(user0.has_perm('Perm2', object0))
    
    def test_get_users(self):
        """
        Tests retrieving list of users with perms on an object
        """
        grant(user0, 'Perm1', object0)
        grant(user0, 'Perm3', object1)
        grant(user1, 'Perm2', object1)
        
        self.assert_(user0 in get_users(object0))
        self.assertFalse(user1 in get_users(object0))
        self.assert_(user0 in get_users(object1))
        self.assert_(user1 in get_users(object1))
        self.assert_(len(get_users(object1))==2)
    
    def test_get_user_permissions(self):
        
        # grant single property
        grant(user0, 'Perm1', object0)
        self.assertEqual([u'Perm1'], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant property again
        grant(user0, 'Perm1', object0)
        self.assertEqual([u'Perm1'], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant second property
        grant(user0, 'Perm2', object0)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant property to another object
        grant(user0, 'Perm2', object1)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(user0, object0))
        self.assertEqual([u'Perm2'], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant perms to other user
        grant(user1, 'Perm3', object0)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(user0, object0))
        self.assertEqual([u'Perm2'], get_user_perms(user0, object1))
        self.assertEqual([u'Perm3'], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
    
    def test_filter(self):
        """
        Test filtering objects
        """
        
        object2 = TestModel.objects.create(name='test2')
        object2.save()
        object3 = TestModel.objects.create(name='test3')
        object3.save()
        
        user0.grant('Perm1', object0)
        user0.grant('Perm2', object1)
        user1.grant('Perm3', object2)
        user1.grant('Perm4', object3)
        
        # retrieve single perm
        self.assert_(object0 in user0.filter_on_perms(TestModel, ['Perm1']))
        self.assert_(object1 in user0.filter_on_perms(TestModel, ['Perm2']))
        self.assert_(object2 in user1.filter_on_perms(TestModel, ['Perm3']))
        self.assert_(object3 in user1.filter_on_perms(TestModel, ['Perm4']))
        
        # retrieve multiple perms
        query = user0.filter_on_perms(TestModel, ['Perm1', 'Perm2', 'Perm3'])
        
        self.assert_(object0 in query)
        self.assert_(object1 in query)
        self.assertEqual(2, query.count())
        query = user1.filter_on_perms(TestModel, ['Perm1','Perm3', 'Perm4'])
        self.assert_(object2 in query)
        self.assert_(object3 in query)
        self.assertEqual(2, query.count())
        
        # retrieve no results
        query = user0.filter_on_perms(TestModel, ['Perm3'])
        self.assertEqual(0, query.count())
        query = user1.filter_on_perms(TestModel, ['Perm1'])
        self.assertEqual(0, query.count())
        
        # extra kwargs
        query = user0.filter_on_perms(TestModel, ['Perm1', 'Perm2', 'Perm3']).filter(name='test0')
        self.assert_(object0 in query)
        self.assertEqual(1, query.count())
        
        # exclude groups
        self.assert_(object0 in user0.filter_on_perms(TestModel, ['Perm1'], groups=False))
        query = user0.filter_on_perms(TestModel, ['Perm1', 'Perm2', 'Perm3'], groups=False)
        self.assert_(object0 in query)
        self.assert_(object1 in query)
        self.assertEqual(2, query.count())
    
    def test_any(self):
        """
        Test checking if a user has perms on any instance of the model
        """

        object2 = TestModel.objects.create(name='test2')
        object2.save()
        object3 = TestModel.objects.create(name='test3')
        object3.save()
        
        user0.grant('Perm1', object0)
        user0.grant('Perm2', object1)
        user1.grant('Perm3', object2)
        
        # check single perm
        self.assert_(user0.perms_on_any(TestModel, ['Perm1']))
        self.assert_(user0.perms_on_any(TestModel, ['Perm2']))
        self.assert_(user1.perms_on_any(TestModel, ['Perm3']))
        self.assert_(user0.perms_on_any(TestModel, ['Perm1'], False))
        self.assert_(user0.perms_on_any(TestModel, ['Perm2'], False))
        self.assert_(user1.perms_on_any(TestModel, ['Perm3'], False))
        
        # check multiple perms
        self.assert_(user0.perms_on_any(TestModel, ['Perm1', 'Perm4']))
        self.assert_(user0.perms_on_any(TestModel, ['Perm1', 'Perm2']))
        self.assert_(user1.perms_on_any(TestModel, ['Perm3', 'Perm4']))
        self.assert_(user0.perms_on_any(TestModel, ['Perm1', 'Perm4'], False))
        self.assert_(user0.perms_on_any(TestModel, ['Perm1', 'Perm2'], False))
        self.assert_(user1.perms_on_any(TestModel, ['Perm3', 'Perm4'], False))
        
        # no results
        self.assertFalse(user0.perms_on_any(TestModel, ['Perm3']))
        self.assertFalse(user1.perms_on_any(TestModel, ['Perm4']))
        self.assertFalse(user0.perms_on_any(TestModel, ['Perm3', 'Perm4']))
        self.assertFalse(user1.perms_on_any(TestModel, ['Perm1', 'Perm4']))
        self.assertFalse(user0.perms_on_any(TestModel, ['Perm3'], False))
        self.assertFalse(user1.perms_on_any(TestModel, ['Perm4'], False))
        self.assertFalse(user0.perms_on_any(TestModel, ['Perm3', 'Perm4'], False))
        self.assertFalse(user1.perms_on_any(TestModel, ['Perm1', 'Perm4'], False))
