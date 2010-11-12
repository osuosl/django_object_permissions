from operator import or_
from warnings import warn

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django import db
from django.db import models
from django.db.models import Q

from models import UserGroup
from object_permissions.signals import granted, revoked


class RegistrationException(Exception):
    pass


class UnknownPermissionException(Exception):
    pass


__all__ = ('register', 'grant', 'revoke', 'grant_group', 'revoke_group', \
               'get_user_perms', 'get_group_perms', 'get_model_perms', \
               'revoke_all', 'revoke_all_group', 'get_users', 'set_user_perms', \
               'set_group_perms', 'get_groups', 'filter_on_perms')

permission_map = {}
"""
A mapping of Models to Models. The key is a registered Model, and the value is
the Model that stores the permissions on that Model.
"""

permissions_for_model = {}
"""
A mapping of Models to lists of permissions defined for that model.
"""

_DELAYED = []
def register(perms, model):
    """
    Register permissions for a Model.

    The permissions should be a list of names of permissions, e.g. ["eat",
    "order", "pay"]. This function will insert a row into the permission table
    if one does not already exist.

    For backwards compatibility, this function can also take a single
    permission instead of a list. This feature should be considered
    deprecated; please fix your code if you depend on this.
    """

    if isinstance(perms, (str, unicode)):
        warn("Using a single permission is deprecated!")
        perms = [perms]

    try:
        return _register(perms, model)
    except db.utils.DatabaseError:
        # there was an error, likely due to a missing table.  Delay this
        # registration.
        _DELAYED.append((perms, model))


def _register(perms, model):
    """
    Real method for registering permissions.

    This method is private; please don't call it from outside code.
    This inner function is required because its logic must also be available
    to call back from _register_delayed for delayed registrations.
    """

    if model in permission_map:
        warn("Tried to double-register %s for permissions!" % model)
        return

    name = "%s_Perms" % model.__name__
    fields = {
        "__module__": "",
        # XXX user xor group null?
        "user": models.ForeignKey(User, null=True,
            related_name="%s_uperms" % model.__name__),
        "group": models.ForeignKey(UserGroup, null=True,
            related_name="%s_gperms" % model.__name__),
        "obj": models.ForeignKey(model,
            related_name="%s_operms" % model.__name__),
    }

    for perm in perms:
        fields[perm] = models.BooleanField(default=False)

    class Meta:
        app_label = "object_permissions"

    fields["Meta"] = Meta

    perm_model = type(name, (models.Model,), fields)
    permission_map[model] = perm_model
    permissions_for_model[model] = perms
    return perm_model


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


if settings.DEBUG:
    # XXX Create test tables only when debug mode.  This model will be used in
    # various unittests.  This is used so that we do not alter any models used
    # in production
    from django.db import models
    class TestModel(models.Model):
        name = models.CharField(max_length=32)
    register(['Perm1', 'Perm2','Perm3','Perm4'], TestModel)


def grant(user, perm, obj):
    """
    Grants a permission to a User
    """

    model = obj.__class__
    
    if perm not in get_model_perms(model):
        raise UnknownPermissionException(perm)
    
    permissions = permission_map[model]
    properties = dict(user=user, obj=obj)

    user_perms, chaff = permissions.objects.get_or_create(**properties)
    setattr(user_perms, perm, True)
    user_perms.save()

    granted.send(sender=user, perm=perm, object=obj)


def grant_group(group, perm, obj):
    """
    Grants a permission to a UserGroup
    """

    model = obj.__class__
    permissions = permission_map[model]
    properties = dict(group=group, obj=obj)

    group_perms, chaff = permissions.objects.get_or_create(**properties)

    # XXX could raise FieldDoesNotExist
    setattr(group_perms, perm, True)
    group_perms.save()

    granted.send(sender=group, perm=perm, object=obj)


def set_user_perms(user, perms, obj):
    """
    Set perms to the list specified
    """

    model = obj.__class__
    permissions = permission_map[model]
    all_perms = dict((p, False) for p in get_model_perms(model))
    for perm in perms:
        all_perms[perm] = True

    user_perms, chaff = permissions.objects.get_or_create(user=user, obj=obj)

    for perm, enabled in all_perms.iteritems():
        setattr(user_perms, perm, enabled)

    user_perms.save()

    return perms


def set_group_perms(group, perms, obj):
    """
    Set group's perms to the list specified
    """

    model = obj.__class__
    permissions = permission_map[model]
    all_perms = dict((p, False) for p in get_model_perms(model))
    for perm in perms:
        all_perms[perm] = True

    group_perms, chaff = permissions.objects.get_or_create(group=group, obj=obj)

    for perm, enabled in all_perms.iteritems():
        setattr(group_perms, perm, enabled)

    group_perms.save()

    return perms


def revoke(user, perm, obj):
    """
    Revokes a permission from a User
    """

    model = obj.__class__
    permissions = permission_map[model]

    try:
        user_perms = permissions.objects.get(user=user, obj=obj)
        setattr(user_perms, perm, False)
        user_perms.save()
        revoked.send(sender=user, perm=perm, object=obj)
        
    except ObjectDoesNotExist:
        # user didnt have permission to begin with
        pass


def revoke_group(group, perm, obj):
    """
    Revokes a permission from a UserGroup
    """

    model = obj.__class__
    permissions = permission_map[model]

    group_perms, chaff = permissions.objects.get_or_create(group=group, obj=obj)

    setattr(group_perms, perm, False)

    revoked.send(sender=group, perm=perm, object=obj)


def revoke_all(user, obj):
    """
    Revokes all permissions from a User
    """

    model = obj.__class__
    permissions = permission_map[model]

    permissions.objects.filter(user=user, obj=obj).delete()


def revoke_all_group(group, obj):
    """
    Revokes all permissions from a User
    """

    model = obj.__class__
    permissions = permission_map[model]

    permissions.objects.filter(group=group, obj=obj).delete()


def get_user_perms(user, obj):
    """
    Return a list of perms that a User has.
    """

    model = obj.__class__
    permissions = permission_map[model]

    try:
        q = permissions.objects.get(user=user, obj=obj)
        return [field.name for field in q._meta.fields
                if isinstance(field, models.BooleanField)
                and getattr(q, field.name)]
    except permissions.DoesNotExist:
        return []


def get_group_perms(group, obj):
    """
    Return a list of perms that a UserGroup has.
    """

    model = obj.__class__
    permissions = permission_map[model]

    try:
        q = permissions.objects.get(group=group, obj=obj)
        return [field.name for field in q._meta.fields
                if isinstance(field, models.BooleanField)
                and getattr(q, field.name)]
    except permissions.DoesNotExist:
        return []


def get_model_perms(model):
    """
    Return a list of perms that a model has registered
    """

    if isinstance(model, models.Model):
        # Instance; get the class
        model = model.__class__
    elif not issubclass(model, models.Model):
        # Not a Model subclass
        raise RegistrationException(
            "%s is neither a model nor instance of one" % model)

    if model not in permissions_for_model:
        raise RegistrationException(
            "Tried to get permissions for unregistered model %s" % model)
    return permissions_for_model[model]


def user_has_perm(user, perm, obj, groups=False):
    """
    check if a UserGroup has a permission on an object
    """
    model = obj.__class__
    if perm not in get_model_perms(model):
        # not a valid permission
        return False
    
    permissions = permission_map[model]
    
    d = {
        perm: True
    }

    if groups:
        return permissions.objects.filter(obj=obj, **d) \
            .filter(Q(user=user) | Q(group__users=user)) \
            .exists()
    else:
        return permissions.objects.filter(user=user, obj=obj, **d).exists()


def group_has_perm(group, perm, obj):
    """
    check if a UserGroup has a permission on an object
    """

    model = obj.__class__
    permissions = permission_map[model]

    d = {
            perm: True,
    }

    return permissions.objects.filter(group=group, obj=obj, **d).exists()


def get_users(obj):
    """
    Return a list of Users with permissions directly on a given object.  This
    will not include users that have permissions via a UserGroup
    """

    model = obj.__class__
    permissions = permission_map[model]

    name = "%s_uperms__obj" % model.__name__
    d = {
            name: obj,
    }

    return User.objects.filter(**d).distinct()


def get_groups(obj):
    """
    Return a list of UserGroups with permissions on a given object
    """

    model = obj.__class__
    permissions = permission_map[model]
    name = "%s_gperms__obj" % model.__name__
    d = {
            name: obj
    }
    return UserGroup.objects.filter(**d).distinct()


def perms_on_any(user, model, perms, groups=True):
    """
    Determines whether the user has any of the listed perms on any instances of
    the Model.  This checks both user permissions and group permissions.

    @param user: user who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @return true if has perms on any instance of model
    """

    permissions = permission_map[model]
    model_perms = get_model_perms(model)
    perms = filter(lambda x: x in model_perms, perms)
    
    # OR all user permission clauses together
    perm_clause = reduce(or_, [Q(**{perm:True}) for perm in perms])
    user_clause = Q(user=user)
    
    if groups:
        # must match either a user or group clause + one of the perm clauses
        group_clause = Q(group__users=user)
        return permissions.objects \
            .filter((user_clause | group_clause) & perm_clause)
    else:
        # must match user clause + one of the perm clauses
        return permissions.objects.filter(user_clause & perm_clause)


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
    model_perms = get_model_perms(model)
    perms = filter(lambda x: x in model_perms, perms)
    name = model.__name__

    d = dict(("%s_operms__%s" % (name, perm), True) for perm in perms)
    
    # OR all user permission clauses together
    perm_clause = reduce(or_, (Q(**{"%s_operms__%s" % (name, perm):True}) \
                               for perm in perms))
    user_clause = Q(**{"%s_operms__user" % name:user})
    
    if groups:
        # must match either a user or group clause + one of the perm clauses
        group_clause = Q(**{"%s_operms__group__users" % name:user})
        query = model.objects.filter((user_clause | group_clause) & perm_clause)
    else:
        # must match user clause + one of the perm clauses
        query = model.objects.filter(user_clause & perm_clause)

    return query.filter(**clauses)


def filter_on_group_perms(group, model, perms, **clauses):
    """
    Filters objects that the UserGroup has permissions on.

    @param usergroup: UserGroup who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @param clauses: additional clauses to be added to the queryset
    @return a queryset of matching objects
    """

    d = {
            "%s_operms__group" % model.__name__: group,
    }

    for perm in perms:
        if perm in get_model_perms(model):
            d["%s_operms__%s" % (model.__name__, perm)] = True

    d.update(clauses)

    return model.objects.filter(**d)


# register internal perms
register(['admin'], UserGroup)


# make some methods available as bound methods
setattr(User, 'grant', grant)
setattr(User, 'revoke', revoke)
setattr(User, 'revoke_all', revoke_all)
setattr(User, 'has_object_perm', user_has_perm)
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
