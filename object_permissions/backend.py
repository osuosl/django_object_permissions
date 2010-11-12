from django.conf import settings
from django.contrib.auth.models import User

from object_permissions.registration import user_has_perm


class ObjectPermBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True

    def __init__(self, *args, **kwargs):
        if hasattr(settings, 'ANONYMOUS_USER_ID'):
            id = settings.ANONYMOUS_USER_ID
            self.anonymous, new = User.objects.get_or_create(id=id, \
                                                        username='anonymous')
            if new:
                self.anonymous.save()
        else:
            self.anonymous = None

    def authenticate(self, username, password):
        """ Empty method, this backend does not authenticate users """
        return None

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_authenticated():
            if self.anonymous:
                user_obj = self.anonymous
            else:
                return False
        
        if obj is None:
            return False
        
        return user_has_perm(user_obj, perm, obj, True)
