
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client

from object_permissions import *
from object_permissions.registration import TestModel, TestModelChild, \
    TestModelChildChild, UnknownPermissionException
from object_permissions.views.permissions import ObjectPermissionForm, \
    ObjectPermissionFormNewUsers

# XXX set global vars to make test code a bit cleaner
user0 = None
user1 = None
superuser = None
obj = None
object0 = None
object1 = None
child = None
perms = None
group = None
c = None
perms = set(['Perm1', 'Perm2', 'Perm3', 'Perm4'])

class TestModelPermissions(TestCase):


    def setUp(self):
        global user0, user1, object0, object1, perms, group

        self.tearDown()
        user0 = User(id=2, username='tester')
        user0.save()
        user1 = User(id=3, username='tester2')
        user1.save()
        
        object0 = TestModel.objects.create(name='test0')
        object0.save()
        object1 = TestModel.objects.create(name='test1')
        object1.save()
        
        group = Group(name='testers')
        group.save()
        group.user_set.add(user0)

    def tearDown(self):
        TestModel.objects.all().delete()
        TestModelChild.objects.all().delete()
        TestModelChildChild.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

        global user0, user1, object0, object1, perms, group
        user0 = None
        user1 = None
        object0 = None
        object1 = None
        group = None

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
        perms1 = perms
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

    def test_get_perms(self):
        """
        tests retrieving list of perms across any instance of a model

        Verifies:
            * No Perms returns empty list
            * some perms returns just that list
            * all perms returns all perms
        """
        self.assertEqual([], user0.get_perms(object0))

        grant(user0, 'Perm1', object0)
        grant(user0, 'Perm3', object1)
        grant(user0, 'Perm4', object1)
        grant(user1, 'Perm2', object0)

        self.assertEqual(['Perm1'], user0.get_perms(object0))

        perms = user0.get_perms(object1)
        self.assertEqual(2, len(perms))
        self.assertEqual(set(['Perm3','Perm4']), set(perms))

    def test_get_perms_any(self):
        """
        tests retrieving list of perms across any instance of a model

        Verifies:
            * No Perms returns empty list
            * some perms returns just that list
            * all perms returns all perms
        """
        self.assertEqual([], user0.get_perms_any(TestModel))
        
        grant(user0, 'Perm1', object0)
        grant(user0, 'Perm3', object1)
        grant(user0, 'Perm4', object1)
        grant(user1, 'Perm2', object0)

        perms = user0.get_perms_any(TestModel)
        self.assertEqual(3, len(perms))
        self.assertEqual(set(['Perm1', 'Perm3', 'Perm4']), set(perms))
    
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
        global user0, user1, superuser, obj, c

        user0 = User(id=2, username='tester0')
        user0.set_password('secret')
        user0.save()
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.save()
        superuser = User(id=4, username='superuser', is_superuser=True)
        superuser.set_password('secret')
        superuser.save()
        
        obj = TestModel.objects.create(name='test')

        c = Client()
    
    def tearDown(self):
        TestModel.objects.all().delete()
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
    
    def test_permissions_generic_add(self):
        """
        Tests adding permissions to a new object using the generic perm view
        """
        url = '/user/%s/permissions/%s/'
        args = (user1.pk, 'TestModel')
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user0.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # invalid class
        self.assert_(c.login(username=superuser.username, password='secret'))
        response = c.get(url % (user1.pk, 'DoesNotExist'))
        self.assertEqual(404, response.status_code)
        
        # invalid user
        response = c.get(url % (-1, 'TestModel'))
        self.assertEqual(404, response.status_code)
        
        # GET - success
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        
        # POST - no perms
        data = {'user':user1.pk, 'obj':obj.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], user1.get_perms(obj))
        
        # POST - no object
        data = {'user':user1.pk, 'permissions':['Perm1']}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], user1.get_perms(obj))
        
        # POST - success
        data = {'user':user1.pk, 'permissions':['Perm1'], 'obj':obj.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/object_row.html')
        self.assertEqual(['Perm1'], user1.get_perms(obj))

    def test_permissions_generic_edit(self):
        """
        Tests adding permissions to a new object using the generic perm view
        """
        url = '/user/%s/permissions/%s/%s/'
        args = (user1.pk, 'TestModel',obj.pk)
        user1.grant('Perm1', obj)
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user0.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # invalid class
        self.assert_(c.login(username=superuser.username, password='secret'))
        response = c.get(url % (user1.pk, 'DoesNotExist',obj.pk))
        self.assertEqual(404, response.status_code)
        
        # invalid user
        response = c.get(url % (-1, 'TestModel',obj.pk))
        self.assertEqual(404, response.status_code)
        
        #invalid object
        response = c.get(url % (user1.pk, 'TestModel',-1))
        self.assertEqual(404, response.status_code)
        
        # GET - success
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        
        # POST - no object
        data = {'user':user1.pk, 'permissions':['Perm2']}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual(['Perm1'], user1.get_perms(obj))
        
        # POST - success
        data = {'user':user1.pk, 'permissions':['Perm2','Perm3'], 'obj':obj.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/object_row.html')
        self.assertEqual(set(['Perm2','Perm3']), set(user1.get_perms(obj)))
        
        # POST - no perms (removes all perms)
        data = {'user':user1.pk, 'obj':obj.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEquals('"TestModel_%s"' % obj.pk, response.content)
        self.assertEqual([], user1.get_perms(obj))
    

class TestObjectPermissionForm(TestCase):
    """ Tests for testing forms for editing permissions """
    
    def setUp(self):
        self.tearDown()
        global obj, child, user, group

        obj = TestModel.objects.create()
        child = TestModelChild.objects.create()
        user = User.objects.create(username='tester')
        group = Group.objects.create(name='test_group')

    def tearDown(self):
        global user, child, obj, group

        if obj:
            if user:
                user.revoke_all(obj)
            if group:
                group.revoke_all(obj)
        TestModel.objects.all().delete()
        TestModelChild.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
    
    def test_trivial(self):
        ObjectPermissionForm(TestModel)
    
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
        choices = ObjectPermissionForm.get_choices(TestModel)
        choices2 = ObjectPermissionForm.get_choices(TestModel)
        choices3 = ObjectPermissionForm.get_choices(TestModel)
        choices4 = ObjectPermissionForm.get_choices(TestModel)
        
        self.assertEqual(id(choices), id(choices2))
        self.assertEqual(id(choices3), id(choices4))
    
    def test_invalid_grantee(self):
        """ tests entering bad id for group or user """
        data = {'user':1234, 'obj':obj.pk, 'permissions':['Perm1']}
        form = ObjectPermissionForm(TestModel, data)
        self.assertFalse(form.is_valid())
        
        data = {'group':1234, 'obj':obj.pk, 'permissions':['Perm1']}
        form = ObjectPermissionForm(TestModel, data)
        self.assertFalse(form.is_valid())
    
    def test_user_group_exclusivity(self):
        """ tests that only a user or a group can be selected """
        global user
        data = {'user':user.pk, 'obj':obj.pk, 'group':group.pk, 'permissions':['Perm1']}
        form = ObjectPermissionForm(TestModel, data)
        self.assertFalse(form.is_valid())
        
        data = {'user':user.pk, 'obj':obj.pk, 'permissions':['Perm1']}
        form = ObjectPermissionForm(TestModel, data)
        self.assert_(form.is_valid(), form.errors)
        self.assertEqual(user, form.cleaned_data['grantee'])
        
        data = {'group':group.pk, 'obj':obj.pk, 'permissions':['Perm1']}
        form = ObjectPermissionForm(TestModel, data)
        self.assert_(form.is_valid())
        self.assertEqual(group, form.cleaned_data['grantee'])


class TestObjectPermissionFormNewUsers(TestCase):
    
    def setUp(self):
        self.tearDown()
        global obj, user
        
        obj = TestModel.objects.create()
        user = User.objects.create(username='tester')

    def tearDown(self):
        global obj, user

        if user:
            user.revoke_all(obj)
        TestModel.objects.all().delete()
        TestModelChild.objects.all().delete()
        User.objects.all().delete()

        obj = None
        user = None
    
    def test_trivial(self):
        ObjectPermissionFormNewUsers(TestModel)

    def test_new_user(self):
        """
        Tests adding a new user
        
        validates:
            * perms must be included
        """
        global user

        data = {'user':user.pk, 'obj':obj.pk}
        form = ObjectPermissionFormNewUsers(TestModel, data)
        self.assertFalse(form.is_valid())
        
        data = {'user':user.pk, 'obj':obj.pk, 'permissions':[]}
        form = ObjectPermissionFormNewUsers(TestModel, data)
        self.assertFalse(form.is_valid())

        data = {'user':user.pk, 'obj':obj.pk, 'permissions':['Perm1']}
        form = ObjectPermissionFormNewUsers(TestModel, data)
        self.assert_(form.is_valid())
        self.assertTrue(form.cleaned_data['new'])
    
    def test_modify_user(self):
        """
        Tests modifying a user's perms
        """
        global user

        user.grant('Perm1', obj)
        data = {'user':user.pk, 'obj':obj.pk, 'permissions':['Perm1']}
        form = ObjectPermissionFormNewUsers(TestModel, data)
        self.assert_(form.is_valid())
        self.assertFalse(form.cleaned_data['new'])
        
        data = {'user':user.pk, 'obj':obj.pk}
        form = ObjectPermissionFormNewUsers(TestModel, data)
        self.assert_(form.is_valid())
        self.assertFalse(form.cleaned_data['new'])
        
        user.grant('Perm1', obj)
        data = {'user':user.pk, 'obj':obj.pk, 'permissions':[]}
        form = ObjectPermissionFormNewUsers(TestModel, data)
        self.assert_(form.is_valid())
        self.assertFalse(form.cleaned_data['new'])