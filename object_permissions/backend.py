from django.conf import settings
from django.db import models, IntegrityError
from django.contrib.auth.models import User

from object_permissions.registration import permission_map, user_has_perm

class ObjectPermBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True

    def __init__(self, *args, **kwargs):
        if hasattr(settings, 'ANONYMOUS_USER_ID'):
            id = settings.ANONYMOUS_USER_ID
            try:
                self.anonymous, new = User.objects.get_or_create(id=id,
                        username='anonymous')
            except IntegrityError:
                # Couldn't get the UID we were told to get, but we were still
                # told to get *an* anonymous user, so we'll make one. Note
                # that this could totally cause a second IntegrityError, which
                # we'll allow to propagate. That's fine; worse things have
                # happened, and it will hopefully LART the user sufficiently.
                self.anonymous, new = User.objects.get_or_create(
                        username='anonymous')
        else:
            self.anonymous = None

    def authenticate(self, username, password):
        """ Empty method, this backend does not authenticate users """
        return None

    def has_perm(self, user_obj, perm, obj=None):
        """
        Return whether the user has the given permission on the given object.
        """

        if not user_obj.is_authenticated():
            if self.anonymous:
                user_obj = self.anonymous
            else:
                return False

        if obj is None:
            return False

        return user_has_perm(user_obj, perm, obj, True)

    def get_all_permissions(self, user_obj, obj=None):
        """
        Get a list of all permissions for the user on the given object.

        This includes permissions given through groups.
        """

        if not user_obj.is_authenticated():
            if self.anonymous:
                user_obj = self.anonymous
            else:
                return []

        if obj is None or not isinstance(obj, models.Model):
            return []

        model = obj.__class__
        permissions = permission_map[model]

        q = permissions.objects.filter(
            models.Q(group__user=user_obj) | models.Q(user=user_obj),
            obj=obj)

        # Extract all set permissions from each row in the query.
        rv = set()
        for row in q:
            rv.update(field.name for field in row._meta.fields
                if isinstance(field, models.IntegerField)
                and getattr(row, field.name))

        return list(rv)

    def get_group_permissions(self, user_obj, obj=None):
        """
        Get a list of permissions for this user's groups on the given object.
        """

        if not user_obj.is_authenticated():
            if self.anonymous:
                user_obj = self.anonymous
            else:
                return []

        if obj is None or not isinstance(obj, models.Model):
            return []

        model = obj.__class__
        permissions = permission_map[model]

        q = permissions.objects.filter(groups__user=user_obj, obj=obj)

        # Extract all set permissions from each row in the query.
        rv = set()
        for row in q:
            rv.update(field.name for field in row._meta.fields
                if isinstance(field, models.BooleanField)
                and getattr(row, field.name))

        return list(rv)
