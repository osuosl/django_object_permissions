from django.contrib.auth.models import User, Group
from django.test import TestCase


from object_permissions import register
from object_permissions.registration import TestModel
from object_permissions.signals import granted, revoked


class TestSignals(TestCase):
    perms = [u'Perm1', u'Perm2', u'Perm3', u'Perm4']
    
    def setUp(self):
        self.tearDown()
        
        self.granted = []
        self.revoked = []
        
        user = User(username='tester')
        user.save()
        group = Group()
        group.save()
        object = TestModel(name='testgroup')
        object.save()
        
        granted.connect(self.granted_receiver)
        revoked.connect(self.revoked_receiver)
        
        g = globals()
        g['user'] = user
        g['group'] = group
        g['object_'] = object
    
    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        TestModel.objects.all().delete()
        
        granted.disconnect(self.granted_receiver)
        revoked.disconnect(self.revoked_receiver)
    
    def granted_receiver(self, sender, perm, object, **kwargs):
        """ receiver for callbacks """
        self.granted.append((sender, perm, object))
    
    def assertGranted(self, sender, perm, object):
        """ asserts that a signal was received """
        t = sender, perm, object
        if not t in self.granted:
            self.fail('Signal was not received: %s, %s, %s' % t)
    
    def assertNotGranted(self, sender, perm, object):
        t = sender, perm, object
        if t in self.granted:
            self.fail('Signal was received: %s, %s, %s' % t)
    
    def revoked_receiver(self, sender, perm, object, **kwargs):
        """ receiver for callbacks """
        self.revoked.append((sender, perm, object))
    
    def assertRevoked(self, sender, perm, object):
        """ asserts that a signal was received """
        t = sender, perm, object
        if not t in self.revoked:
            self.fail('Signal was not received: %s, %s, %s' % t)
    
    def assertNotRevoked(self, sender, perm, object):
        """ asserts that a signal was received """
        t = sender, perm, object
        if t in self.revoked:
            self.fail('Signal was received: %s, %s, %s' % t)
    
    def test_grant(self):
        user.grant('Perm1', object_)
        self.assertGranted(user, 'Perm1', object_)
        
        # test second grant
        self.granted = []
        user.grant('Perm1', object_)
        self.assertNotGranted(user, 'Perm1', object_)
    
    def test_revoke(self):
        user.grant('Perm1', object_)
        user.revoke('Perm1', object_)
        self.assertRevoked(user, 'Perm1', object_)
        
        # test second revoke
        self.revoked = []
        user.revoke('Perm1', object_)
        self.assertNotRevoked(user, 'Perm1', object_)
    
    def test_grant_group(self):
        group.grant('Perm1', object_)
        self.assertGranted(group, 'Perm1', object_)
        
        # test second grant
        self.granted = []
        group.grant('Perm1', object_)
        self.assertNotGranted(group, 'Perm1', object_)
    
    def test_revoke_group(self):
        group.grant('Perm1', object_)
        group.revoke('Perm1', object_)
        self.assertRevoked(group, 'Perm1', object_)
        
        # test second revoke
        self.revoked = []
        group.revoke('Perm1', object_)
        self.assertNotRevoked(group, 'Perm1', object_)
    
    def test_revoke_all(self):
        user.grant('Perm1', object_)
        user.grant('Perm2', object_)
        user.revoke_all(object_)
        self.assertRevoked(user, 'Perm1', object_)
        self.assertRevoked(user, 'Perm2', object_)
        
        # test second revoke
        self.revoked = []
        user.revoke_all(object_)
        self.assertFalse(self.revoked)
    
    
    def test_revoke_all_group(self):
        group.grant('Perm1', object_)
        group.grant('Perm2', object_)
        group.revoke_all(object_)
        self.assertRevoked(group, 'Perm1', object_)
        self.assertRevoked(group, 'Perm2', object_)
        
        # test second revoke
        self.revoked = []
        user.revoke_all(object_)
        self.assertFalse(self.revoked)
    
    def test_set_group_perms(self):
        user.grant('Perm1', object_)
        user.set_perms(['Perm2','Perm3'], object_)
        self.assertRevoked(user, 'Perm1', object_)
        self.assertGranted(user, 'Perm2', object_)
        self.assertGranted(user, 'Perm3', object_)
    
    def test_set_user_perms(self):
        group.grant('Perm1', object_)
        group.set_perms(['Perm2','Perm3'], object_)
        self.assertRevoked(group, 'Perm1', object_)
        self.assertGranted(group, 'Perm2', object_)
        self.assertGranted(group, 'Perm3', object_)
