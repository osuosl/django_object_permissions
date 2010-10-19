from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django import db
from django.db import models

from models import ObjectPermission, ObjectPermissionType, UserGroup, \
    GroupObjectPermission
import object_permissions
from object_permissions.signals import granted, revoked


__all__ = ('register', 'grant', 'revoke', 'grant_group', 'revoke_group', \
               'get_user_perms', 'get_group_perms', 'get_model_perms', \
               'revoke_all', 'revoke_all_group', 'get_users', 'set_user_perms', \
               'set_group_perms', 'get_groups', 'filter_on_perms')


_DELAYED = []
def register(perm, model):
    """
    Register a permission for a Model.  This will insert a row into the
    permission table if one does not already exist.
    """
    try:
        _register(perm, model)
    except db.utils.DatabaseError:
        # there was an error, likely due to a missing table.  Delay this
        # registration.
        _DELAYED.append((perm, model))


def _register(perm, model):
    """
    Real method for registering permissions.  This inner function is used
    because it must also be called back from _register_delayed
    """
    ct = ContentType.objects.get_for_model(model)
    obj, new = ObjectPermissionType.objects \
               .get_or_create(name=perm, content_type=ct)
    if new:
        obj.save()


def _register_delayed(**kwargs):
    """
    Register all permissions that were delayed waiting for database tables
    to be created
    """
    try:
        for args in _DELAYED:
            _register(*args)
        models.signals.post_syncdb.disconnect(_register_delayed)
    except db.utils.DatabaseError:
        # still waiting for models in other apps to be created
        pass
models.signals.post_syncdb.connect(_register_delayed)


def grant(user, perm, object):
    """
    Grants a permission to a User
    """
    ct = ContentType.objects.get_for_model(object)
    pt = ObjectPermissionType.objects.get(name=perm, content_type=ct)
    properties = dict(user=user, permission=pt, object_id=object.id)
    if not ObjectPermission.objects.filter(**properties).exists():
        ObjectPermission(**properties).save()
        granted.send(sender=user, perm=perm, object=object)


def grant_group(group, perm, object):
    """
    Grants a permission to a UserGroup
    """
    ct = ContentType.objects.get_for_model(object)
    pt = ObjectPermissionType.objects.get(name=perm, content_type=ct)
    properties = dict(group=group, permission=pt, object_id=object.id)
    if not GroupObjectPermission.objects.filter(**properties).exists():
        GroupObjectPermission(**properties).save()
        granted.send(sender=group, perm=perm, object=object)


def set_user_perms(user, perms, object):
    """
    Set perms to the list specified
    """
    if perms:
        for perm in perms:
            grant(user, perm, object)
        model_perms = get_model_perms(object)
        for perm in [p for p in model_perms if p not in perms]:
            revoke(user, perm, object)
    else:
        revoke_all(user, object)
    return perms


def set_group_perms(group, perms, object):
    """
    Set User's perms to the list specified
    """
    if perms:
        for perm in perms:
            grant_group(group, perm, object)
        model_perms = get_model_perms(object)
        for perm in [p for p in model_perms if p not in perms]:
            revoke_group(group, perm, object)
    else:
        revoke_all_group(group, object)
    
    return perms


def revoke(user, perm, object):
    """
    Revokes a permission from a User
    """
    ct = ContentType.objects.get_for_model(object)
    query = ObjectPermission.objects \
                .filter(user=user, object_id=object.id,  \
                    permission__content_type=ct, permission__name=perm)
    if query.exists():
        query.delete()
        revoked.send(sender=user, perm=perm, object=object)


def revoke_all(user, object):
    """
    Revokes all permissions from a User
    """
    ct = ContentType.objects.get_for_model(object)
    query = ObjectPermission.objects \
        .filter(user=user, object_id=object.id, permission__content_type=ct)
    if revoked.receivers:
        # only perform second query if there are receivers attached
        perms = list(query.values_list('permission__name', flat=True))
        query.delete()
        for perm in perms:
            revoked.send(sender=user, perm=perm, object=object)
    else:
        query.delete()
    

def revoke_all_group(group, object):
    """
    Revokes all permissions from a User
    """
    ct = ContentType.objects.get_for_model(object)
    query = GroupObjectPermission.objects \
        .filter(group=group, object_id=object.id, permission__content_type=ct)
    if revoked.receivers:
        # only perform second query if there are receivers attached
        perms = list(query.values_list('permission__name', flat=True))
        query.delete()
        for perm in perms:
            revoked.send(sender=group, perm=perm, object=object)
    else:
        query.delete()


def revoke_group(group, perm, object):
    """
    Revokes a permission from a UserGroup
    """
    ct = ContentType.objects.get_for_model(object)
    query = GroupObjectPermission.objects \
                .filter(group=group, object_id=object.id,  \
                    permission__content_type=ct, permission__name=perm) 
    if query.exists():
        query.delete()
        revoked.send(sender=group, perm=perm, object=object)


def get_user_perms(user, object):
    """
    Return a list of perms that a User has.
    """
    ct = ContentType.objects.get_for_model(object)
    query = ObjectPermission.objects \
        .filter(user=user, object_id=object.id, permission__content_type=ct) \
        .values_list('permission__name', flat=True)
    return list(query)


def get_group_perms(group, object):
    """
    Return a list of perms that a UserGroup has.
    """
    ct = ContentType.objects.get_for_model(object)
    query = GroupObjectPermission.objects \
        .filter(group=group, object_id=object.id, permission__content_type=ct) \
        .values_list('permission__name', flat=True)
    return list(query)


def get_model_perms(model):
    """
    Return a list of perms that a model has registered
    """
    ct = ContentType.objects.get_for_model(model)
    query = ObjectPermissionType.objects.filter(content_type=ct) \
            .values_list('name', flat=True)
    return list(query)


def group_has_perm(group, perm, object):
    """
    check if a UserGroup has a permission on an object
    """
    if object is None:
        return False
    
    ct = ContentType.objects.get_for_model(object)
    return GroupObjectPermission.objects \
        .filter(group=group, object_id=object.id, \
                permission__name=perm, permission__content_type=ct) \
        .exists()


def get_users(object):
    """
    Return a list of Users with permissions directly on a given object.  This
    will not include users that have permissions via a UserGroup
    """
    ct = ContentType.objects.get_for_model(object)
    return User.objects.filter(
            object_permissions__permission__content_type=ct, \
            object_permissions__object_id=object.id).distinct()


def get_groups(object):
    """
    Return a list of UserGroups with permissions on a given object
    """
    ct = ContentType.objects.get_for_model(object)
    return UserGroup.objects.filter(
            object_permissions__permission__content_type=ct, \
            object_permissions__object_id=object.id).distinct()


def perms_on_any(user, model, perms):
    """
    Determines whether the user has any of the listed perms on any instances of
    the Model.  This checks both user permissions and group permissions.
    
    @param user: user who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @return true if has perms on any instance of model
    """
    ct = ContentType.objects.get_for_model(model)
    
    # permissions user has
    if ObjectPermission.objects.filter(
            user = user,
            permission__content_type=ct,
            permission__name__in=perms
        ).exists():
            return True
    
    # permissions user's groups have
    if GroupObjectPermission.objects.filter(
            group__users = user,
            permission__content_type=ct,
            permission__name__in=perms
        ).exists():
            return True
    
    return False


def filter_on_perms(user, model, perms, groups=True, **clauses):
    """
    Filters objects that the User has permissions on.  This includes any objects
    the user has permissions based on belonging to a UserGroup.
    
    @param user: user who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @param groups: include perms the user has from membership in UserGroups
    @param clauses: additional clauses to be added to the queryset
    @return a queryset of matching objects
    """
    ct = ContentType.objects.get_for_model(model)
    
    # permissions user has
    ids = list(ObjectPermission.objects.filter(
            user=user,
            permission__content_type=ct,
            permission__name__in=perms
        ).values_list('object_id', flat=True))
    
    # permissions user's groups have
    if groups:
        ids += list(GroupObjectPermission.objects.filter(
                group__users=user,
                permission__content_type=ct,
                permission__name__in=perms
            ).values_list('object_id', flat=True))
    
    return model.objects.filter(id__in=ids, **clauses)


def filter_on_group_perms(usergroup, model, perms, **clauses):
    """
    Filters objects that the UserGroup has permissions on.
    
    @param usergroup: UserGroup who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @param clauses: additional clauses to be added to the queryset
    @return a queryset of matching objects
    """
    ct = ContentType.objects.get_for_model(model)
    
    # permissions user's groups have
    ids = list(GroupObjectPermission.objects.filter(
            group=usergroup,
            permission__content_type=ct,
            permission__name__in=perms
        ).values_list('object_id', flat=True))
    
    return model.objects.filter(id__in=ids, **clauses)


# register internal perms
register('admin', UserGroup)


# make some methods available as bound methods
setattr(User, 'grant', grant)
setattr(User, 'revoke', revoke)
setattr(User, 'revoke_all', revoke_all)
setattr(User, 'get_perms', get_user_perms)
setattr(User, 'set_perms', set_user_perms)
setattr(User, 'filter_on_perms', filter_on_perms)
setattr(User, 'perms_on_any', perms_on_any)

setattr(UserGroup, 'grant', grant_group)
setattr(UserGroup, 'revoke', revoke_group)
setattr(UserGroup, 'revoke_all', revoke_all_group)
setattr(UserGroup, 'has_perm', group_has_perm)
setattr(UserGroup, 'get_perms', get_group_perms)
setattr(UserGroup, 'set_perms', set_group_perms)
setattr(UserGroup, 'filter_on_perms', filter_on_group_perms)