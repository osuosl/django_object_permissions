from django.contrib.auth.models import User
from django.test import TestCase

from object_permissions import grant, revoke, get_user_perms, revoke_all, \
    get_users, set_user_perms, user_has_any_perms
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
        grant(self.user0, 'Perm1', self.object0)
        self.assert_(self.user0.has_perm('Perm1', self.object0))
        self.assertFalse(self.user0.has_perm('Perm1', self.object1))
        self.assertFalse(self.user1.has_perm('Perm1', self.object0))
        self.assertFalse(self.user1.has_perm('Perm1', self.object1))
        
        # grant property again
        grant(self.user0, 'Perm1', self.object0)
        self.assert_(self.user0.has_perm('Perm1', self.object0))
        self.assertFalse(self.user0.has_perm('Perm1', self.object1))
        self.assertFalse(self.user1.has_perm('Perm1', self.object0))
        self.assertFalse(self.user1.has_perm('Perm1', self.object1))
        
        # grant second property
        grant(self.user0, 'Perm2', self.object0)
        self.assert_(self.user0.has_perm('Perm1', self.object0))
        self.assertFalse(self.user0.has_perm('Perm1', self.object1))
        self.assertFalse(self.user1.has_perm('Perm1', self.object0))
        self.assertFalse(self.user1.has_perm('Perm1', self.object1))
        self.assert_(self.user0.has_perm('Perm2', self.object0))
        self.assertFalse(self.user0.has_perm('Perm2', self.object1))
        self.assertFalse(self.user1.has_perm('Perm2', self.object0))
        self.assertFalse(self.user1.has_perm('Perm2', self.object1))
        
        # grant property to another object
        grant(self.user0, 'Perm2', self.object1)
        self.assert_(self.user0.has_perm('Perm1', self.object0))
        self.assertFalse(self.user0.has_perm('Perm1', self.object1))
        self.assertFalse(self.user1.has_perm('Perm1', self.object0))
        self.assertFalse(self.user1.has_perm('Perm1', self.object1))
        self.assert_(self.user0.has_perm('Perm2', self.object0))
        self.assert_(self.user0.has_perm('Perm2', self.object1))
        self.assertFalse(self.user1.has_perm('Perm2', self.object0))
        self.assertFalse(self.user1.has_perm('Perm2', self.object1))
        
        # grant perms to other user
        grant(self.user1, 'Perm3', self.object0)
        self.assert_(self.user0.has_perm('Perm1', self.object0))
        self.assertFalse(self.user0.has_perm('Perm1', self.object1))
        self.assertFalse(self.user1.has_perm('Perm1', self.object0))
        self.assertFalse(self.user1.has_perm('Perm1', self.object1))
        self.assert_(self.user0.has_perm('Perm2', self.object0))
        self.assert_(self.user0.has_perm('Perm2', self.object1))
        self.assertFalse(self.user1.has_perm('Perm2', self.object0))
        self.assertFalse(self.user1.has_perm('Perm2', self.object1))
        self.assert_(self.user1.has_perm('Perm3', self.object0))
        
        def grant_unknown():
            grant(self.user1, 'UnknownPerm', self.object0)
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
        revoke(self.user0, 'Perm1', self.object0)
        
        for perm in self.perms:
            grant(self.user0, perm, self.object0)
            grant(self.user0, perm, self.object1)
            grant(self.user1, perm, self.object0)
            grant(self.user1, perm, self.object1)
        
        # revoke single perm
        revoke(self.user0, 'Perm1', self.object0)
        self.assertEqual([u'Perm2', u'Perm3', u'Perm4'], get_user_perms(self.user0, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user0, self.object1))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))
        
        # revoke a second perm
        revoke(self.user0, 'Perm3', self.object0)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user0, self.object1))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))
        
        # revoke from another object
        revoke(self.user0, 'Perm3', self.object1)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object1))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))
        
        # revoke from another user
        revoke(self.user1, 'Perm4', self.object0)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))
        
        # revoke perm user does not have
        revoke(self.user0, 'Perm1', self.object0)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))
        
        # revoke perm that does not exist
        revoke(self.user0, 'DoesNotExist', self.object0)
        self.assertEqual([u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], get_user_perms(self.user0, self.object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))
    
    def test_revoke_all(self):
        """
        Test revoking all permissions from a user
        
        Verifies
            * revoked properties are only removed from the correct user/obj combinations
            * revoking property user does not have does not give an error
            * revoking unknown permission raises error
        """
        for perm in self.perms:
            grant(self.user0, perm, self.object0)
            grant(self.user0, perm, self.object1)
            grant(self.user1, perm, self.object0)
            grant(self.user1, perm, self.object1)

        revoke_all(self.user0, self.object0)
        self.assertEqual([], get_user_perms(self.user0, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user0, self.object1))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))

        revoke_all(self.user0, self.object1)
        self.assertEqual([], get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))

        revoke_all(self.user1, self.object0)
        self.assertEqual([], get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))
        self.assertEqual(self.perms, get_user_perms(self.user1, self.object1))

        revoke_all(self.user1, self.object1)
        self.assertEqual([], get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))
        self.assertEqual([], get_user_perms(self.user1, self.object1))

    def test_set_perms(self):
        """
        Test setting perms to an exact set
        """
        perms1 = self.perms
        perms2 = ['Perm1', 'Perm2']
        perms3 = ['Perm2', 'Perm3']
        perms4 = []

        # grant single property
        set_user_perms(self.user0, perms1, self.object0)
        self.assertEqual(perms1, get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))

        set_user_perms(self.user0, perms2, self.object0)
        self.assertEqual(perms2, get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))

        set_user_perms(self.user0, perms3, self.object0)
        self.assertEqual(perms3, get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))

        # remove perms
        set_user_perms(self.user0, perms4, self.object0)
        self.assertEqual(perms4, get_user_perms(self.user0, self.object0))
        self.assertFalse(self.user0.TestModel_uperms.filter(obj=self.object0).exists())
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))

        set_user_perms(self.user0, perms2, self.object1)
        self.assertEqual(perms4, get_user_perms(self.user0, self.object0))
        self.assertEqual(perms2, get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))

        set_user_perms(self.user1, perms1, self.object0)
        self.assertEqual(perms4, get_user_perms(self.user0, self.object0))
        self.assertEqual(perms2, get_user_perms(self.user0, self.object1))
        self.assertEqual(perms1, get_user_perms(self.user1, self.object0))
    
    def test_has_perm(self):
        """
        Additional tests for has_perms

        Verifies:
            * None object always returns false
            * Nonexistent perm returns false
            * Perm user does not possess returns false
        """
        grant(self.user0, 'Perm1', self.object0)

        self.assertTrue(self.user0.has_perm('Perm1', self.object0))
        self.assertFalse(self.user0.has_perm('Perm1', None))
        self.assertFalse(self.user0.has_perm('DoesNotExist'), self.object0)
        self.assertFalse(self.user0.has_perm('Perm2', self.object0))

    def test_get_users(self):
        """
        Tests retrieving list of users with perms on an object
        """
        grant(self.user0, 'Perm1', self.object0)
        grant(self.user0, 'Perm3', self.object1)
        grant(self.user1, 'Perm2', self.object1)

        self.assert_(self.user0 in get_users(self.object0))
        self.assertFalse(self.user1 in get_users(self.object0))
        self.assert_(self.user0 in get_users(self.object1))
        self.assert_(self.user1 in get_users(self.object1))
        self.assert_(len(get_users(self.object1))==2)
    
    def test_get_user_permissions(self):
        
        # grant single property
        grant(self.user0, 'Perm1', self.object0)
        self.assertEqual([u'Perm1'], get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))
        self.assertEqual([], get_user_perms(self.user1, self.object1))
        
        # grant property again
        grant(self.user0, 'Perm1', self.object0)
        self.assertEqual([u'Perm1'], get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))
        self.assertEqual([], get_user_perms(self.user1, self.object1))
        
        # grant second property
        grant(self.user0, 'Perm2', self.object0)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(self.user0, self.object0))
        self.assertEqual([], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))
        self.assertEqual([], get_user_perms(self.user1, self.object1))
        
        # grant property to another object
        grant(self.user0, 'Perm2', self.object1)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(self.user0, self.object0))
        self.assertEqual([u'Perm2'], get_user_perms(self.user0, self.object1))
        self.assertEqual([], get_user_perms(self.user1, self.object0))
        self.assertEqual([], get_user_perms(self.user1, self.object1))
        
        # grant perms to other user
        grant(self.user1, 'Perm3', self.object0)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(self.user0, self.object0))
        self.assertEqual([u'Perm2'], get_user_perms(self.user0, self.object1))
        self.assertEqual([u'Perm3'], get_user_perms(self.user1, self.object0))
        self.assertEqual([], get_user_perms(self.user1, self.object1))
    
    def test_filter(self):
        """
        Test filtering objects
        """
        
        object2 = TestModel.objects.create(name='test2')
        object2.save()
        object3 = TestModel.objects.create(name='test3')
        object3.save()
        
        self.user0.grant('Perm1', self.object0)
        self.user0.grant('Perm2', self.object1)
        self.user1.grant('Perm3', object2)
        self.user1.grant('Perm4', object3)
        
        # retrieve single perm
        self.assert_(self.object0 in self.user0.filter_on_perms(TestModel, ['Perm1']))
        self.assert_(self.object1 in self.user0.filter_on_perms(TestModel, ['Perm2']))
        self.assert_(object2 in self.user1.filter_on_perms(TestModel, ['Perm3']))
        self.assert_(object3 in self.user1.filter_on_perms(TestModel, ['Perm4']))
        
        # retrieve multiple perms
        query = self.user0.filter_on_perms(TestModel, ['Perm1', 'Perm2', 'Perm3'])
        
        self.assert_(self.object0 in query)
        self.assert_(self.object1 in query)
        self.assertEqual(2, query.count())
        query = self.user1.filter_on_perms(TestModel, ['Perm1','Perm3', 'Perm4'])
        self.assert_(object2 in query)
        self.assert_(object3 in query)
        self.assertEqual(2, query.count())
        
        # retrieve no results
        query = self.user0.filter_on_perms(TestModel, ['Perm3'])
        self.assertEqual(0, query.count())
        query = self.user1.filter_on_perms(TestModel, ['Perm1'])
        self.assertEqual(0, query.count())
        
        # extra kwargs
        query = self.user0.filter_on_perms(TestModel, ['Perm1', 'Perm2', 'Perm3']).filter(name='test0')
        self.assert_(self.object0 in query)
        self.assertEqual(1, query.count())
        
        # exclude groups
        self.assert_(self.object0 in self.user0.filter_on_perms(TestModel, ['Perm1'], groups=False))
        query = self.user0.filter_on_perms(TestModel, ['Perm1', 'Perm2', 'Perm3'], groups=False)
        self.assert_(self.object0 in query)
        self.assert_(self.object1 in query)
        self.assertEqual(2, query.count())
    
    def test_any(self):
        """
        Test checking if a user has perms on any instance of the model
        """

        object2 = TestModel.objects.create(name='test2')
        object2.save()
        object3 = TestModel.objects.create(name='test3')
        object3.save()
        
        self.user0.grant('Perm1', self.object0)
        self.user0.grant('Perm2', self.object1)
        self.user1.grant('Perm3', object2)
        
        # check single perm
        self.assert_(self.user0.perms_on_any(TestModel, ['Perm1']))
        self.assert_(self.user0.perms_on_any(TestModel, ['Perm2']))
        self.assert_(self.user1.perms_on_any(TestModel, ['Perm3']))
        self.assert_(self.user0.perms_on_any(TestModel, ['Perm1'], False))
        self.assert_(self.user0.perms_on_any(TestModel, ['Perm2'], False))
        self.assert_(self.user1.perms_on_any(TestModel, ['Perm3'], False))
        
        # check multiple perms
        self.assert_(self.user0.perms_on_any(TestModel, ['Perm1', 'Perm4']))
        self.assert_(self.user0.perms_on_any(TestModel, ['Perm1', 'Perm2']))
        self.assert_(self.user1.perms_on_any(TestModel, ['Perm3', 'Perm4']))
        self.assert_(self.user0.perms_on_any(TestModel, ['Perm1', 'Perm4'], False))
        self.assert_(self.user0.perms_on_any(TestModel, ['Perm1', 'Perm2'], False))
        self.assert_(self.user1.perms_on_any(TestModel, ['Perm3', 'Perm4'], False))
        
        # no results
        self.assertFalse(self.user0.perms_on_any(TestModel, ['Perm3']))
        self.assertFalse(self.user1.perms_on_any(TestModel, ['Perm4']))
        self.assertFalse(self.user0.perms_on_any(TestModel, ['Perm3', 'Perm4']))
        self.assertFalse(self.user1.perms_on_any(TestModel, ['Perm1', 'Perm4']))
        self.assertFalse(self.user0.perms_on_any(TestModel, ['Perm3'], False))
        self.assertFalse(self.user1.perms_on_any(TestModel, ['Perm4'], False))
        self.assertFalse(self.user0.perms_on_any(TestModel, ['Perm3', 'Perm4'], False))
        self.assertFalse(self.user1.perms_on_any(TestModel, ['Perm1', 'Perm4'], False))

    def test_has_any_perm(self):
        """
        Test the user_has_any_perm() function.
        """

        self.assertFalse(user_has_any_perms(self.user0, self.object0))
        self.user0.grant("Perm1", self.object0)
        self.assertTrue(user_has_any_perms(self.user0, self.object0))
