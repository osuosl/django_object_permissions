
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client

from object_permissions import *
from object_permissions.registration import TestModel, TestModelChild, \
    TestModelChildChild, UnknownPermissionException
from object_permissions.views.permissions import ObjectPermissionForm, \
    ObjectPermissionFormNewUsers

class TestModelPermissions(TestCase):
    perms = set(['Perm1', 'Perm2', 'Perm3', 'Perm4'])

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
        
        self.group = Group(name='testers')
        self.group.save()
        self.group.user_set.add(self.user0)
        
        dict_ = globals()
        dict_['user0']=self.user0
        dict_['user1']=self.user1
        dict_['object0']=self.object0
        dict_['object1']=self.object1
        dict_['perms']=self.perms
        dict_['group']=self.group

    def tearDown(self):
        TestModel.objects.all().delete()
        TestModelChild.objects.all().delete()
        TestModelChildChild.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_trivial(self):
        pass

    def test_registration(self):
        """
        Test that permissions were registered correctly
        """
        perms1 = get_model_perms(TestModel)
        perms2 = get_model_perms(TestModelChild)
        
        self.assert_('Perm1' in perms1)
        self.assert_('Perm2' in perms1)
        self.assert_('Perm3' in perms1)
        self.assert_('Perm4' in perms1)
        
        self.assert_(isinstance(perms2, (dict,)))
        self.assert_('Perm1' in perms2)
        self.assert_('Perm2' in perms2)
        self.assert_('Perm3' in perms2)
        self.assert_('Perm4' in perms2)

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
        self.assertEqual(set(['Perm2', u'Perm3', 'Perm4']), set(get_user_perms(user0, object0)))
        self.assertEqual(perms, set(get_user_perms(user0, object1)))
        self.assertEqual(perms, set(get_user_perms(user1, object0)))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
        
        # revoke a second perm
        revoke(user0, 'Perm3', object0)
        self.assertEqual(set(['Perm2', 'Perm4']), set(get_user_perms(user0, object0)))
        self.assertEqual(perms, set(get_user_perms(user0, object1)))
        self.assertEqual(perms, set(get_user_perms(user1, object0)))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
        
        # revoke from another object
        revoke(user0, 'Perm3', object1)
        self.assertEqual(set(['Perm2', 'Perm4']), set(get_user_perms(user0, object0)))
        self.assertEqual(set(['Perm1', 'Perm2', 'Perm4']), set(get_user_perms(user0, object1)))
        self.assertEqual(perms, set(get_user_perms(user1, object0)))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
        
        # revoke from another user
        revoke(user1, 'Perm4', object0)
        self.assertEqual(set(['Perm2', 'Perm4']), set(get_user_perms(user0, object0)))
        self.assertEqual(set(['Perm1', 'Perm2', 'Perm4']), set(get_user_perms(user0, object1)))
        self.assertEqual(set(['Perm1', 'Perm2', u'Perm3']), set(get_user_perms(user1, object0)))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
        
        # revoke perm user does not have
        revoke(user0, 'Perm1', object0)
        self.assertEqual(set(['Perm2', 'Perm4']), set(get_user_perms(user0, object0)))
        self.assertEqual(set(['Perm1', 'Perm2', 'Perm4']), set(get_user_perms(user0, object1)))
        self.assertEqual(set(['Perm1', 'Perm2', u'Perm3']), set(get_user_perms(user1, object0)))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
        
        # revoke perm that does not exist
        revoke(user0, 'DoesNotExist', object0)
        self.assertEqual(set(['Perm2', 'Perm4']), set(get_user_perms(user0, object0)))
        self.assertEqual(set(['Perm1', 'Perm2', 'Perm4']), set(get_user_perms(user0, object1)))
        self.assertEqual(set(['Perm1', 'Perm2', u'Perm3']), set(get_user_perms(user1, object0)))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
    
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
        self.assertEqual(perms, set(get_user_perms(user0, object1)))
        self.assertEqual(perms, set(get_user_perms(user1, object0)))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
        
        revoke_all(user0, object1)
        self.assertEqual([], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual(perms, set(get_user_perms(user1, object0)))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
        
        revoke_all(user1, object0)
        self.assertEqual([], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual(perms, set(get_user_perms(user1, object1)))
        
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
        perms2 = set(['Perm1', 'Perm2'])
        perms3 = set(['Perm2', 'Perm3'])
        perms4 = []

        # grant single property
        set_user_perms(user0, perms1, object0)
        self.assertEqual(perms1, set(get_user_perms(user0, object0)))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user0, perms2, object0)
        self.assertEqual(perms2, set(get_user_perms(user0, object0)))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user0, perms3, object0)
        self.assertEqual(perms3, set(get_user_perms(user0, object0)))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        # remove perms
        set_user_perms(user0, perms4, object0)
        self.assertEqual(perms4, get_user_perms(user0, object0))
        self.assertFalse(user0.TestModel_uperms.filter(obj=object0).exists())
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user0, perms2, object1)
        self.assertEqual(perms4, get_user_perms(user0, object0))
        self.assertEqual(perms2, set(get_user_perms(user0, object1)))
        self.assertEqual([], get_user_perms(user1, object0))
        
        set_user_perms(user1, perms1, object0)
        self.assertEqual(perms4, get_user_perms(user0, object0))
        self.assertEqual(perms2, set(get_user_perms(user0, object1)))
        self.assertEqual(perms1, set(get_user_perms(user1, object0)))
    
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
    
    def test_get_users_any(self):
        """
        Tests retrieving list of users with perms on an object
        """
        user0.set_perms(['Perm1', 'Perm2'], object0)
        user0.set_perms(['Perm1', 'Perm3'], object1)
        user1.set_perms(['Perm2'], object1)
        
        # no perms
        self.assertFalse(user1 in get_users_any(object0, ['Perm1']))
        
        # explicit any perms
        self.assert_(user0 in get_users_any(object0))
        self.assert_(user0 in get_users_any(object1))
        self.assertFalse(user1 in get_users_any(object0))
        self.assert_(user1 in get_users_any(object1))
        
        # has perms, but not the right one
        self.assertFalse(user0 in get_users_any(object0, ['Perm3']))
        
        # has one perm, but not all
        self.assert_(user0 in get_users_any(object0, ['Perm1','Perm3']))
        self.assert_(user0 in get_users_any(object1, ['Perm1','Perm2']))
        
        # has single perm
        self.assert_(user0 in get_users_any(object0, ['Perm1']))
        self.assert_(user0 in get_users_any(object0, ['Perm2']))
        self.assert_(user1 in get_users_any(object1, ['Perm2']))
        
        # has multiple perms
        self.assert_(user0 in get_users_any(object0, ['Perm1','Perm2']))
        self.assert_(user0 in get_users_any(object1, ['Perm1','Perm3']))
        
        # retry all tests via groups
        # reset perms for group test
        user0.revoke_all(object1)
        group.set_perms(['Perm1', 'Perm3'], object1)
        
        # ---------------------------------------------------------------------
        # retry tests including groups, should be same set of results since
        # user0 now has same permissions except object1 perms are through a
        # group
        # ---------------------------------------------------------------------
        # no perms
        self.assertFalse(user1 in get_users_any(object0, ['Perm1']))
        
        # explicit any perms
        self.assert_(user0 in get_users_any(object0))
        self.assert_(user0 in get_users_any(object1))
        self.assertFalse(user1 in get_users_any(object0))
        self.assert_(user1 in get_users_any(object1))
        
        # has perms, but not the right one
        self.assertFalse(user0 in get_users_any(object0, ['Perm3']))
        
        # has one perm, but not all
        self.assert_(user0 in get_users_any(object0, ['Perm1','Perm3']))
        self.assert_(user0 in get_users_any(object1, ['Perm1','Perm2']))
        
        # has single perm
        self.assert_(user0 in get_users_any(object0, ['Perm1']))
        self.assert_(user0 in get_users_any(object0, ['Perm2']))
        self.assert_(user1 in get_users_any(object1, ['Perm2']))
        
        # has multiple perms
        self.assert_(user0 in get_users_any(object0, ['Perm1','Perm2']))
        self.assert_(user0 in get_users_any(object1, ['Perm1','Perm3']))
        
        # ----------------------------
        # retry tests excluding groups
        # ----------------------------
        # no perms
        self.assertFalse(user1 in get_users_any(object0, ['Perm1'], groups=False))
        
        # explicit any perms
        self.assert_(user0 in get_users_any(object0, groups=False))
        self.assertFalse(user0 in get_users_any(object1, groups=False))
        self.assertFalse(user1 in get_users_any(object0, groups=False))
        self.assert_(user1 in get_users_any(object1, groups=False))
        
        # has perms, but not the right one
        self.assertFalse(user0 in get_users_any(object0, ['Perm3'], groups=False))
        
        # has one perm, but not all
        self.assert_(user0 in get_users_any(object0, ['Perm1','Perm3'], groups=False))
        self.assertFalse(user0 in get_users_any(object1, ['Perm1','Perm2'], groups=False))
        
        # has single perm
        self.assert_(user0 in get_users_any(object0, ['Perm1'], groups=False))
        self.assert_(user0 in get_users_any(object0, ['Perm2'], groups=False))
        self.assert_(user1 in get_users_any(object1, ['Perm2'], groups=False))
        
        # has multiple perms
        self.assert_(user0 in get_users_any(object0, ['Perm1','Perm2'], groups=False))
        self.assertFalse(user0 in get_users_any(object1, ['Perm1','Perm3'], groups=False))
    
    def test_get_users_all(self):
        """
        Tests retrieving list of users with perms on an object
        """
        user0.set_perms(['Perm1', 'Perm2'], object0)
        user0.set_perms(['Perm1', 'Perm3'], object1)
        user1.set_perms(['Perm2'], object1)
        
        # no perms
        self.assertFalse(user1 in get_users_all(object0, ['Perm1']))
        
        # has perms, but not the right one
        self.assertFalse(user0 in get_users_all(object0, ['Perm3']))
        
        # has one perm, but not all
        self.assertFalse(user0 in get_users_all(object0, ['Perm1','Perm3']))
        self.assertFalse(user0 in get_users_all(object1, ['Perm1','Perm2']))
        
        # has single perm
        self.assert_(user0 in get_users_all(object0, ['Perm1']))
        self.assert_(user0 in get_users_all(object0, ['Perm2']))
        self.assert_(user1 in get_users_all(object1, ['Perm2']))
        
        # has multiple perms
        self.assert_(user0 in get_users_all(object0, ['Perm1','Perm2']))
        self.assert_(user0 in get_users_all(object1, ['Perm1','Perm3']))
        
        # retry all tests via groups
        # reset perms for group test
        user0.revoke_all(object1)
        group.set_perms(['Perm1', 'Perm3'], object1)
        
        # ---------------------------------------------------------------------
        # retry tests including groups, should be same set of results since
        # user0 now has same permissions except object1 perms are through a
        # group
        # ---------------------------------------------------------------------
        # no perms
        self.assertFalse(user1 in get_users_all(object0, ['Perm1']))
        
        # has perms, but not the right one
        self.assertFalse(user0 in get_users_all(object0, ['Perm3']))
        
        # has one perm, but not all
        self.assertFalse(user0 in get_users_all(object0, ['Perm1','Perm3']))
        self.assertFalse(user0 in get_users_all(object1, ['Perm1','Perm2']))
        
        # has single perm
        self.assert_(user0 in get_users_all(object0, ['Perm1']))
        self.assert_(user0 in get_users_all(object0, ['Perm2']))
        self.assert_(user1 in get_users_all(object1, ['Perm2']))
        
        # has multiple perms
        self.assert_(user0 in get_users_all(object0, ['Perm1','Perm2']))
        self.assert_(user0 in get_users_all(object1, ['Perm1','Perm3']))
        
        # ----------------------------
        # retry tests excluding groups
        # ----------------------------
        # no perms
        self.assertFalse(user1 in get_users_all(object0, ['Perm1'], groups=False))
        
        # has perms, but not the right one
        self.assertFalse(user0 in get_users_all(object0, ['Perm3'], groups=False))
        
        # has one perm, but not all
        self.assertFalse(user0 in get_users_all(object0, ['Perm1','Perm3'], groups=False))
        self.assertFalse(user0 in get_users_all(object1, ['Perm1','Perm2'], groups=False))
        
        # has single perm
        self.assert_(user0 in get_users_all(object0, ['Perm1'], groups=False))
        self.assert_(user0 in get_users_all(object0, ['Perm2'], groups=False))
        self.assert_(user1 in get_users_all(object1, ['Perm2'], groups=False))
        
        # has multiple perms
        self.assert_(user0 in get_users_all(object0, ['Perm1','Perm2'], groups=False))
        self.assertFalse(user0 in get_users_all(object1, ['Perm1','Perm3'], groups=False))
    
    def test_get_user_permissions(self):
        
        # grant single property
        grant(user0, 'Perm1', object0)
        self.assertEqual(['Perm1'], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant property again
        grant(user0, 'Perm1', object0)
        self.assertEqual(['Perm1'], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant second property
        grant(user0, 'Perm2', object0)
        self.assertEqual(set(['Perm1', 'Perm2']), set(get_user_perms(user0, object0)))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant property to another object
        grant(user0, 'Perm2', object1)
        self.assertEqual(set(['Perm1', 'Perm2']), set(get_user_perms(user0, object0)))
        self.assertEqual(['Perm2'], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant perms to other user
        grant(user1, 'Perm3', object0)
        self.assertEqual(set(['Perm1', 'Perm2']), set(get_user_perms(user0, object0)))
        self.assertEqual(['Perm2'], get_user_perms(user0, object1))
        self.assertEqual(['Perm3'], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
    
    def test_get_objects_any_perms(self):
        """
        Test retrieving objects with any matching perms
        """
        
        object2 = TestModel.objects.create(name='test2')
        object2.save()
        object3 = TestModel.objects.create(name='test3')
        object3.save()
        
        user0.grant('Perm1', object0)
        user0.grant('Perm2', object1)
        user1.grant('Perm3', object2)
        user1.grant('Perm4', object3)
        
        # implicit any
        self.assert_(object0 in user0.get_objects_any_perms(TestModel))
        self.assert_(object1 in user0.get_objects_any_perms(TestModel))
        self.assertFalse(object2 in user0.get_objects_any_perms(TestModel))
        self.assert_(object2 in user1.get_objects_any_perms(TestModel))
        self.assert_(object3 in user1.get_objects_any_perms(TestModel))
        
        # retrieve single perm
        self.assert_(object0 in user0.get_objects_any_perms(TestModel, ['Perm1']))
        self.assert_(object1 in user0.get_objects_any_perms(TestModel, ['Perm2']))
        self.assert_(object2 in user1.get_objects_any_perms(TestModel, ['Perm3']))
        self.assert_(object3 in user1.get_objects_any_perms(TestModel, ['Perm4']))
        
        # retrieve multiple perms
        query = user0.get_objects_any_perms(TestModel, ['Perm1', 'Perm2', 'Perm3'])
        
        self.assert_(object0 in query)
        self.assert_(object1 in query)
        self.assertEqual(2, query.count())
        query = user1.get_objects_any_perms(TestModel, ['Perm1','Perm3', 'Perm4'])
        self.assert_(object2 in query)
        self.assert_(object3 in query)
        self.assertEqual(2, query.count())
        
        # retrieve no results
        query = user0.get_objects_any_perms(TestModel, ['Perm3'])
        self.assertEqual(0, query.count())
        query = user1.get_objects_any_perms(TestModel, ['Perm1'])
        self.assertEqual(0, query.count())
        
        # extra kwargs
        query = user0.get_objects_any_perms(TestModel, ['Perm1', 'Perm2', 'Perm3']).filter(name='test0')
        self.assert_(object0 in query)
        self.assertEqual(1, query.count())
        
        # exclude groups
        self.assert_(object0 in user0.get_objects_any_perms(TestModel, ['Perm1'], groups=False))
        query = user0.get_objects_any_perms(TestModel, ['Perm1', 'Perm2', 'Perm3'], groups=False)
        self.assert_(object0 in query)
        self.assert_(object1 in query)
        self.assertEqual(2, query.count())
    
    def test_get_objects_any_perms_related(self):
        """
        Test retrieving objects with any matching perms and related model
        options
        """
        object2 = TestModel.objects.create(name='test2')
        object2.save()
        
        child0 = TestModelChild.objects.create(parent=object0)
        child1 = TestModelChild.objects.create(parent=object1)
        child2 = TestModelChild.objects.create(parent=object2)
        child3 = TestModelChild.objects.create(parent=object2)
        child0.save()
        child1.save()
        child2.save()
        
        childchild = TestModelChildChild.objects.create(parent=child0)
        childchild.save()
        
        user0.grant('Perm1', object0)  # perms on both
        user0.grant('Perm2', child0)   # perms on both
        user0.grant('Perm3', object1)  # perm on parent only (child 1)
        user0.grant('Perm4', child2)   # perm on child only
        user0.grant('Perm1', childchild)
        
        # related field with implicit perms
        query = user0.get_objects_any_perms(TestModelChild, parent=None)
        self.assertEqual(3, len(query))
        self.assert_(child0 in query, 'user should have perms on parent and directly')
        self.assert_(child1 in query, 'user should have perms on parent')
        self.assert_(child2 in query, 'user should have perms on parent, and directly')
        self.assertFalse(child3 in query, 'user should have no perms on this object or its parent')
        
        # related field with single perms
        query = user0.get_objects_any_perms(TestModelChild, parent=['Perm3'])
        self.assertEqual(3, len(query))
        self.assert_(child0 in query, 'user should have perms on parent and directly')
        self.assert_(child1 in query, 'user should have perms on parent')
        self.assert_(child2 in query, 'user should have perms on parent')
        self.assertFalse(child3 in query, 'user should have no perms on this object or its parent')
        
        # related field with multiple perms
        query = user0.get_objects_any_perms(TestModelChild, parent=['Perm1','Perm3'])
        self.assertEqual(3, len(query))
        self.assert_(child0 in query, 'user should have perms on parent and directly')
        self.assert_(child1 in query, 'user should have perms on parent')
        self.assert_(child2 in query, 'user should have perms on parent')
        self.assertFalse(child3 in query, 'user should have no perms on this object or its parent')
        
        # mix of direct and related perms
        query = user0.get_objects_any_perms(TestModelChild, perms=['Perm4'], parent=['Perm1'])
        self.assertEqual(2, len(query))
        self.assert_(child0 in query, 'user should have perms on parent and directly')
        self.assertFalse(child1 in query, 'user should not have perms on parent')
        self.assert_(child2 in query, 'user should have perms directly')
        self.assertFalse(child3 in query, 'user should have no perms on this object or its parent')
        
        # multiple relations
        query = user0.get_objects_any_perms(TestModelChildChild, parent=['Perm2'], parent__parent=['Perm1'])
        self.assertEqual(1, len(query))
        self.assert_(childchild in query)
    
    def test_get_objects_all_perms(self):
        """
        Test retrieving objects that have all matching perms
        """
        
        object2 = TestModel.objects.create(name='test2')
        object2.save()
        object3 = TestModel.objects.create(name='test3')
        object3.save()
        
        user0.grant('Perm1', object0)
        user0.grant('Perm2', object0)
        user0.grant('Perm4', object1)
        user1.grant('Perm3', object2)
        user1.grant('Perm4', object2)
        
        # retrieve single perm
        self.assert_(object0 in user0.get_objects_all_perms(TestModel, ['Perm1']))
        self.assert_(object1 in user0.get_objects_all_perms(TestModel, ['Perm4']))
        self.assert_(object2 in user1.get_objects_all_perms(TestModel, ['Perm3']))
        self.assert_(object2 in user1.get_objects_all_perms(TestModel, ['Perm4']))
        
        # retrieve multiple perms
        query = user0.get_objects_all_perms(TestModel, ['Perm1', 'Perm2'])
        
        self.assert_(object0 in query)
        self.assertFalse(object1 in query)
        self.assertEqual(1, query.count())
        query = user1.get_objects_all_perms(TestModel, ['Perm3', 'Perm4'])
        self.assert_(object2 in query)
        self.assertFalse(object3 in query)
        self.assertEqual(1, query.count())
        
        # retrieve no results
        self.assertFalse(user0.get_objects_all_perms(TestModel, ['Perm3']).exists())
        self.assertFalse(user0.get_objects_all_perms(TestModel, ['Perm1','Perm4']).exists())
        self.assertFalse(user1.get_objects_all_perms(TestModel, ['Perm1']).exists())
        
        # extra kwargs
        query = user0.get_objects_all_perms(TestModel, ['Perm1', 'Perm2']).filter(name='test0')
        self.assert_(object0 in query)
        self.assertEqual(1, query.count())
        
        # exclude groups
        self.assert_(object0 in user0.get_objects_all_perms(TestModel, ['Perm1'], groups=False))
        query = user0.get_objects_all_perms(TestModel, ['Perm1', 'Perm2'], groups=False)
        self.assert_(object0 in query)
        self.assertFalse(object1 in query)
        self.assertEqual(1, query.count())
    
    def test_get_objects_all_perms_related(self):
        """
        Test retrieving objects with all matching perms and related model
        options
        """
        child0 = TestModelChild.objects.create(parent=object0)
        child1 = TestModelChild.objects.create(parent=object0)
        child2 = TestModelChild.objects.create(parent=object1)
        child0.save()
        child1.save()
        child2.save()
        
        childchild = TestModelChildChild.objects.create(parent=child0)
        childchild.save()
        
        user0.grant('Perm1', object0)
        user0.grant('Perm1', object1)
        user0.grant('Perm2', object1)
        
        user0.grant('Perm1', child0)
        user0.grant('Perm1', child1)
        user0.grant('Perm2', child1)
        user0.grant('Perm1', childchild)
        
        # related field with single perms
        query = user0.get_objects_all_perms(TestModelChild, perms=['Perm1'], parent=['Perm1'])
        self.assertEqual(2, len(query))
        self.assert_(child0 in query)
        self.assert_(child1 in query)
        self.assertFalse(child2 in query)
        
        # related field with single perms - has parent but not child
        query = user0.get_objects_all_perms(TestModelChild, perms=['Perm4'], parent=['Perm1'])
        self.assertEqual(0, len(query))
        
        # related field with single perms - has child but not parent
        query = user0.get_objects_all_perms(TestModelChild, perms=['Perm1'], parent=['Perm4'])
        self.assertEqual(0, len(query))
        
        # related field with multiple perms
        query = user0.get_objects_all_perms(TestModelChild, perms=['Perm1'], parent=['Perm1','Perm2'])
        self.assertEqual(1, len(query))
        self.assertFalse(child0 in query)
        self.assert_(child1 in query)
        self.assertFalse(child2 in query)
        
        # multiple relations
        query = user0.get_objects_all_perms(TestModelChildChild, perms=['Perm1'], parent=['Perm1'], parent__parent=['Perm1'])
        self.assertEqual(1, len(query))
        self.assert_(childchild in query)
    
    def test_get_all_objects_any_perms(self):
        """
        Test retrieving all objects from all models
        """
        object2 = TestModel.objects.create(name='test2')
        object2.save()
        object3 = TestModel.objects.create(name='test3')
        object3.save()
        object4 = TestModel.objects.create(name='test4')
        object4.save()
        
        user0.grant('Perm1', object0)
        user0.grant('Perm2', object1)
        user0.grant('Perm4', object1)
        
        perm_dict = user0.get_all_objects_any_perms()
        self.assert_(isinstance(perm_dict, (dict,)))
        self.assert_(TestModel in perm_dict, perm_dict.keys())
        self.assert_(object0 in perm_dict[TestModel])
        self.assert_(object1 in perm_dict[TestModel])
        self.assertFalse(object2 in perm_dict[TestModel])
        self.assertFalse(object3 in perm_dict[TestModel])
        self.assertFalse(object4 in perm_dict[TestModel])
        
        # no perms
        perm_dict = user1.get_all_objects_any_perms()
        self.assert_(isinstance(perm_dict, (dict,)))
        self.assert_(TestModel in perm_dict, perm_dict.keys())
        self.assertEqual(0, perm_dict[TestModel].count())
        
        # ---------------------------------------------------------------------
        # retry tests including groups, should be same set of results since
        # user0 now has same permissions except object1 perms are through a
        # group
        # ---------------------------------------------------------------------
        user0.revoke_all(object1)
        group.set_perms(['Perm1', 'Perm3'], object1)
        
        perm_dict = user0.get_all_objects_any_perms()
        self.assert_(isinstance(perm_dict, (dict,)))
        self.assert_(TestModel in perm_dict, perm_dict.keys())
        self.assert_(object0 in perm_dict[TestModel])
        self.assert_(object1 in perm_dict[TestModel])
        self.assertFalse(object2 in perm_dict[TestModel])
        self.assertFalse(object3 in perm_dict[TestModel])
        self.assertFalse(object4 in perm_dict[TestModel])
        
        # ----------------------------
        # retry tests excluding groups
        # ----------------------------
        perm_dict = user0.get_all_objects_any_perms(groups=False)
        self.assert_(isinstance(perm_dict, (dict,)))
        self.assert_(TestModel in perm_dict, perm_dict.keys())
        self.assert_(object0 in perm_dict[TestModel])
        self.assertFalse(object1 in perm_dict[TestModel])
        self.assertFalse(object2 in perm_dict[TestModel])
        self.assertFalse(object3 in perm_dict[TestModel])
        self.assertFalse(object4 in perm_dict[TestModel])
    
    def test_has_any_on_model(self):
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
        self.assert_(user0.has_any_perms(TestModel, ['Perm1']))
        self.assert_(user0.has_any_perms(TestModel, ['Perm2']))
        self.assert_(user1.has_any_perms(TestModel, ['Perm3']))
        self.assert_(user0.has_any_perms(TestModel, ['Perm1'], False))
        self.assert_(user0.has_any_perms(TestModel, ['Perm2'], False))
        self.assert_(user1.has_any_perms(TestModel, ['Perm3'], False))
        
        # check multiple perms
        self.assert_(user0.has_any_perms(TestModel, ['Perm1', 'Perm4']))
        self.assert_(user0.has_any_perms(TestModel, ['Perm1', 'Perm2']))
        self.assert_(user1.has_any_perms(TestModel, ['Perm3', 'Perm4']))
        self.assert_(user0.has_any_perms(TestModel, ['Perm1', 'Perm4'], False))
        self.assert_(user0.has_any_perms(TestModel, ['Perm1', 'Perm2'], False))
        self.assert_(user1.has_any_perms(TestModel, ['Perm3', 'Perm4'], False))
        
        # no results
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm3']))
        self.assertFalse(user1.has_any_perms(TestModel, ['Perm4']))
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm3', 'Perm4']))
        self.assertFalse(user1.has_any_perms(TestModel, ['Perm1', 'Perm4']))
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm3'], False))
        self.assertFalse(user1.has_any_perms(TestModel, ['Perm4'], False))
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm3', 'Perm4'], False))
        self.assertFalse(user1.has_any_perms(TestModel, ['Perm1', 'Perm4'], False))
        
        # ---------------------------------------------------------------------
        # retry tests including groups, should be same set of results since
        # user0 now has same permissions except object1 perms are through a
        # group
        # ---------------------------------------------------------------------
        user0.revoke_all(object1)
        group.grant("Perm2", object1)
        
        # check single perm
        self.assert_(user0.has_any_perms(TestModel, ['Perm1']))
        self.assert_(user0.has_any_perms(TestModel, ['Perm2']))
        self.assert_(user1.has_any_perms(TestModel, ['Perm3']))
        
        # check multiple perms
        self.assert_(user0.has_any_perms(TestModel, ['Perm1', 'Perm4']))
        self.assert_(user0.has_any_perms(TestModel, ['Perm1', 'Perm2']))
        self.assert_(user1.has_any_perms(TestModel, ['Perm3', 'Perm4']))
        
        # no results
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm3']))
        self.assertFalse(user1.has_any_perms(TestModel, ['Perm4']))
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm3', 'Perm4']))
        self.assertFalse(user1.has_any_perms(TestModel, ['Perm1', 'Perm4']))
        
        # ----------------------------
        # retry tests excluding groups
        # ----------------------------
        # check single perm
        self.assert_(user0.has_any_perms(TestModel, ['Perm1'], False))
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm2'], False))
        self.assert_(user1.has_any_perms(TestModel, ['Perm3'], False))
        
        # check multiple perms
        self.assert_(user0.has_any_perms(TestModel, ['Perm1', 'Perm4'], False))
        self.assert_(user0.has_any_perms(TestModel, ['Perm1', 'Perm2'], False))
        self.assert_(user1.has_any_perms(TestModel, ['Perm3', 'Perm4'], False))
        
        # no results
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm3'], False))
        self.assertFalse(user1.has_any_perms(TestModel, ['Perm4'], False))
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm2', 'Perm4'], False))
        self.assertFalse(user0.has_any_perms(TestModel, ['Perm3', 'Perm4'], False))
        self.assertFalse(user1.has_any_perms(TestModel, ['Perm1', 'Perm4'], False))

    def test_has_any_perm(self):
        """
        Test the user_has_any_perm() function.
        """
        # no perms
        self.assertFalse(user_has_any_perms(user0, object0))
        self.assertFalse(user_has_any_perms(user0, object0, ['Perm1', 'Perm2']))
        self.assertFalse(user_has_any_perms(user0, object0, groups=True))
        self.assertFalse(user_has_any_perms(user0, object0, ['Perm1', 'Perm2']))
        
        # single perm
        user0.grant("Perm1", object0)
        user1.grant("Perm2", object0)
        self.assertTrue(user_has_any_perms(user0, object0))
        self.assertTrue(user_has_any_perms(user1, object0))
        self.assertTrue(user_has_any_perms(user0, object0, ['Perm1', 'Perm2']))
        self.assertTrue(user_has_any_perms(user1, object0, ['Perm1', 'Perm2']))
        user0.revoke_all(object0)
        user1.revoke_all(object0)
        
        
        # perm on group, but not checking
        group.grant("Perm3", object0)
        self.assertFalse(user_has_any_perms(user0, object0, groups=False))
        self.assertFalse(user_has_any_perms(user0, object0, ['Perm1', 'Perm3'], groups=False))
        
        # perm on group, checking groups
        self.assertTrue(user_has_any_perms(user0, object0, groups=True))
        self.assertTrue(user_has_any_perms(user0, object0, ['Perm1', 'Perm3']))

    def test_has_all_on_model(self):
        """
        Test checking if a user has perms on any instance of the model
        """

        object2 = TestModel.objects.create(name='test2')
        object2.save()
        object3 = TestModel.objects.create(name='test3')
        object3.save()
        
        user0.grant('Perm1', object0)
        user0.grant('Perm2', object0)
        user0.grant('Perm2', object1)
        user1.grant('Perm3', object2)
        
        # check single perm
        self.assert_(user0.has_all_perms(TestModel, ['Perm1']))
        self.assert_(user0.has_all_perms(TestModel, ['Perm2']))
        self.assert_(user1.has_all_perms(TestModel, ['Perm3']))
        self.assert_(user0.has_all_perms(TestModel, ['Perm1'], False))
        self.assert_(user0.has_all_perms(TestModel, ['Perm2'], False))
        self.assert_(user1.has_all_perms(TestModel, ['Perm3'], False))
        
        # check multiple perms
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm1', 'Perm4']))
        self.assert_(user0.has_all_perms(TestModel, ['Perm1', 'Perm2']))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm3', 'Perm4']))
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm1', 'Perm4'], False))
        self.assert_(user0.has_all_perms(TestModel, ['Perm1', 'Perm2'], False))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm3', 'Perm4'], False))
        
        # no results
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm3']))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm4']))
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm3', 'Perm4']))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm1', 'Perm4']))
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm3'], False))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm4'], False))
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm3', 'Perm4'], False))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm1', 'Perm4'], False))
        
        # ---------------------------------------------------------------------
        # retry tests including groups, should be same set of results since
        # user0 now has same permissions except object1 perms are through a
        # group
        # ---------------------------------------------------------------------
        user0.revoke_all(object1)
        group.grant("Perm2", object1)
        
        # check single perm
        self.assert_(user0.has_all_perms(TestModel, ['Perm1']))
        self.assert_(user0.has_all_perms(TestModel, ['Perm2']))
        self.assert_(user1.has_all_perms(TestModel, ['Perm3']))
        
        # check multiple perms
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm1', 'Perm4']))
        self.assert_(user0.has_all_perms(TestModel, ['Perm1', 'Perm2']))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm3', 'Perm4']))
        
        # no results
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm3']))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm4']))
        self.assertFalse(user0.has_all_perms(TestModel, ['Perm3', 'Perm4']))
        self.assertFalse(user1.has_all_perms(TestModel, ['Perm1', 'Perm4']))


    def test_has_all_perm(self):
        """
        Test the user_has_any_perm() function.
        """
        # no perms
        self.assertFalse(user_has_all_perms(user0, object0, ['Perm1', 'Perm2']))
        self.assertFalse(user_has_all_perms(user0, object0, ['Perm1', 'Perm2']))
        
        # single perm
        user0.grant("Perm1", object0)
        user1.grant("Perm2", object0)
        self.assertFalse(user_has_all_perms(user0, object0, ['Perm1', 'Perm2']))
        self.assertFalse(user_has_all_perms(user1, object0, ['Perm1', 'Perm2']))
        self.assert_(user_has_all_perms(user0, object0, ['Perm1']))
        self.assert_(user_has_all_perms(user1, object0, ['Perm2']))
        user0.revoke_all(object0)
        user1.revoke_all(object0)
        
        # perm on group, but not checking
        group.grant("Perm3", object0)
        self.assertFalse(user_has_all_perms(user0, object0, ['Perm3'], groups=False))
        
        # perm on group, checking groups
        self.assert_(user_has_all_perms(user0, object0, ['Perm3']))


class TestPermissionViews(TestCase):
    """ tests for user specific test views """
    
    def setUp(self):
        self.tearDown()
        
        user0 = User(id=2, username='tester0')
        user0.set_password('secret')
        user0.save()
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.save()
        
        d = globals()
        d['c'] = Client()
        d['user0'] = user0
        d['user1'] = user1
    
    def tearDown(self):
        User.objects.all().delete()
    
    def test_permissions_all(self):
        """ tests view for returning all permissions across all objects """
        url = '/user/%s/permissions/all'
        
        # anonymous user
        response = c.get(url % user1.pk, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user0.username, password='secret'))
        response = c.get(url % user1.pk)
        self.assertEqual(403, response.status_code)
        
        # unknown user
        user0.is_superuser = True
        user0.save()
        response = c.get(url % 123456)
        self.assertEqual(404, response.status_code)
        
        # superuser
        response = c.get(url % user1.pk)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/objects.html')


class TestObjectPermissionForm(TestCase):
    """ Tests for testing forms for editing permissions """
    
    def setUp(self):
        self.tearDown()
        
        obj = TestModel.objects.create()
        child = TestModelChild.objects.create()
        user = User.objects.create(username='tester')
        group = Group.objects.create(name='test_group')
        
        d = globals()
        d['obj'] = obj
        d['child'] = child
        d['user'] = user
        d['group'] = group
    
    def tearDown(self):
        if 'obj' in globals():
            if 'user' in globals():
                user.revoke_all(obj)
            if 'group' in globals():
                group.revoke_all(obj)
        TestModel.objects.all().delete()
        TestModelChild.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
    
    def test_trivial(self):
        form = ObjectPermissionForm(obj)
    
    def test_choices_generation(self):
        """ tests that permissions choices lists are generated correctly """
        choices = ObjectPermissionForm.get_choices(obj)
        
        self.assertEqual(4, len(choices))
        choice3, choice2, choice1, choice4 = choices
        
        perm, display = choice1
        self.assertEqual('Perm1', perm)
        self.assertEqual(display, {'label':'Perm One','description':'The first permission'})
        
        perm, display = choice2
        self.assertEqual('Perm2', perm)
        self.assertEqual(display, {'label':'Perm2','description':'The second permission'})
        
        perm, display = choice3
        self.assertEqual('Perm3', perm)
        self.assertEqual(display, {'label':'Perm Three'})
        
        perm, display = choice4
        self.assertEqual('Perm4', perm)
        self.assertEqual(display, {'label':'Perm4'})
    
    def test_choices_cache(self):
        """ tests that choices lists are cached """
        choices = ObjectPermissionForm.get_choices(obj)
        choices2 = ObjectPermissionForm.get_choices(obj)
        choices3 = ObjectPermissionForm.get_choices(obj)
        choices4 = ObjectPermissionForm.get_choices(obj)
        
        self.assertEqual(id(choices), id(choices2))
        self.assertEqual(id(choices3), id(choices4))
    
    def test_invalid_grantee(self):
        """ tests entering bad id for group or user """
        data = {'user':1234, 'permissions':['Perm1']}
        form = ObjectPermissionForm(obj, data)
        self.assertFalse(form.is_valid())
        
        data = {'group':1234, 'permissions':['Perm1']}
        form = ObjectPermissionForm(obj, data)
        self.assertFalse(form.is_valid())
    
    def test_user_group_exclusivity(self):
        """ tests that only a user or a group can be selected """
        
        data = {'user':user.pk, 'group':group.pk, 'permissions':['Perm1']}
        form = ObjectPermissionForm(obj, data)
        self.assertFalse(form.is_valid())
        
        data = {'user':user.pk, 'permissions':['Perm1']}
        form = ObjectPermissionForm(obj, data)
        self.assert_(form.is_valid(), form.errors)
        self.assertEqual(user, form.cleaned_data['grantee'])
        
        data = {'group':group.pk, 'permissions':['Perm1']}
        form = ObjectPermissionForm(obj, data)
        self.assert_(form.is_valid())
        self.assertEqual(group, form.cleaned_data['grantee'])


class TestObjectPermissionFormNewUsers(TestCase):
    
    def setUp(self):
        self.tearDown()
        
        obj = TestModel.objects.create()
        user = User.objects.create(username='tester')
        
        d = globals()
        d['obj'] = obj
        d['user'] = user
    
    def tearDown(self):
        if 'user' in globals():
            user.revoke_all(obj)
        TestModel.objects.all().delete()
        TestModelChild.objects.all().delete()
        User.objects.all().delete()
    
    def test_trivial(self):
        form = ObjectPermissionFormNewUsers(obj)


    def test_new_user(self):
        """
        Tests adding a new user
        
        validates:
            * perms must be included
        """
        data = {'user':user.pk}
        form = ObjectPermissionFormNewUsers(obj, data)
        self.assertFalse(form.is_valid())
        
        data = {'user':user.pk, 'permissions':[]}
        form = ObjectPermissionFormNewUsers(obj, data)
        self.assertFalse(form.is_valid())

        data = {'user':user.pk, 'permissions':['Perm1']}
        form = ObjectPermissionFormNewUsers(obj, data)
        self.assert_(form.is_valid())
        self.assertTrue(form.cleaned_data['new'])
    
    def test_modify_user(self):
        """
        Tests modifying a user's perms
        """
        user.grant('Perm1', obj)
        data = {'user':user.pk, 'permissions':['Perm1']}
        form = ObjectPermissionFormNewUsers(obj, data)
        self.assert_(form.is_valid())
        self.assertFalse(form.cleaned_data['new'])
        
        data = {'user':user.pk}
        form = ObjectPermissionFormNewUsers(obj, data)
        self.assert_(form.is_valid())
        self.assertFalse(form.cleaned_data['new'])
        
        user.grant('Perm1', obj)
        data = {'user':user.pk, 'permissions':[]}
        form = ObjectPermissionFormNewUsers(obj, data)
        self.assert_(form.is_valid())
        self.assertFalse(form.cleaned_data['new'])