from operator import or_
from warnings import warn

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django import db
from django.db import models
from django.db.models import Model
from django.db.models import Q, F

from object_permissions.signals import granted, revoked

"""
Registration functions.

This is the meat and gravy of the entire app.

In order to use permissions with a Model, that Model's permissions must be
registered in advance. Registration can only be done once per Model, at model
definition time, and must include all permissions for that Model.

>>> register(["spam", "eggs", "toast"], Breakfast)

Once registered, permissions may be set for any pairing of an instance of that
Model and an instance of a User or Group.

Technical tl;dr: Registration can only happen once because Object Permissions
dynamically creates new models to store the permissions for a specific model.
Since the dynamic models need to be database-backed, they can't be altered
once defined and they must be defined before validation. We'd like to offer
our sincerest assurance that, even though dynamic models are dangerous, our
highly trained staff has expertly wrestled these majestic, fascinating,
terrifying beasts into cages, and now they are yours to tame and own. Buy one
today!

...Okay, that got weird. But you get the point. Only register() a model once.
"""

class RegistrationException(Exception):
    pass


class UnknownPermissionException(Exception):
    pass


class InvalidQueryException(Exception):
    """ exception raised when there are invalid arguments for a query.  This is
    only raised when the arguments won't result in a more verbose error by
    django """
    pass


__all__ = (
    'register',
    'grant', 'grant_group',
    'revoke', 'revoke_group',
    'get_user_perms', 'get_group_perms',
    'revoke_all', 'revoke_all_group',
    'set_user_perms', 'set_group_perms',
    'get_users', 'get_users_all', 'get_users_any',
    'get_groups', 'get_groups_all', 'get_groups_any',
    "user_has_any_perms", "group_has_any_perms",
    "user_has_all_perms", "group_has_all_perms",
    'get_model_perms',
    'filter_on_perms',
)

permission_map = {}
"""
A mapping of Models to Models. The key is a registered Model, and the value is
the Model that stores the permissions on that Model.
"""

permissions_for_model = {}
"""
A mapping of Models to lists of permissions defined for that model.
"""

forbidden = set([
    "full_clean",
    "clean_fields",
    "clean",
    "validate_unique",
    "save",
    "pk",
    "delete",
    "get_absolute_url",
])
"""
Names reserved by Django for Model instances.
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

    for perm in perms:
        if perm in forbidden:
            raise RegistrationException("Permission %s is a reserved name!")

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
        "group": models.ForeignKey(Group, null=True,
            related_name="%s_gperms" % model.__name__),
        "obj": models.ForeignKey(model,
            related_name="operms"),
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
    Register all permissions that were delayed waiting for database tables to
    be created.

    Don't call this from outside code.
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
    # XXX Create test tables only when debug mode.  These models will be used in
    # various unittests.  This is used so that we do not alter any models used
    # in production
    from django.db import models
    class TestModel(models.Model):
        name = models.CharField(max_length=32)
    class TestModelChild(models.Model):
        parent = models.ForeignKey(TestModel, null=True, related_name='child')
    class TestModelChildChild(models.Model):
        parent = models.ForeignKey(TestModelChild, null=True, related_name='child')
    register(['Perm1', 'Perm2','Perm3','Perm4'], TestModel)
    register(['Perm1', 'Perm2','Perm3','Perm4'], TestModelChild)
    register(['Perm1', 'Perm2','Perm3','Perm4'], TestModelChildChild)

def grant(user, perm, obj):
    """
    Grant a permission to a User.
    """

    model = obj.__class__

    if perm not in get_model_perms(model):
        raise UnknownPermissionException(perm)

    permissions = permission_map[model]

    try:
        user_perms = permissions.objects.get(user=user, obj=obj)
    except permissions.DoesNotExist:
        user_perms = permissions(user=user, obj=obj)

    # XXX could raise FieldDoesNotExist
    if not getattr(user_perms, perm):
        setattr(user_perms, perm, True)
        user_perms.save()
        
        granted.send(sender=user, perm=perm, object=obj)


def grant_group(group, perm, obj):
    """
    Grant a permission to a Group.
    """

    model = obj.__class__
    if perm not in get_model_perms(model):
        raise UnknownPermissionException(perm)
    
    permissions = permission_map[model]

    try:
        group_perms = permissions.objects.get(group=group, obj=obj)
    except permissions.DoesNotExist:
        group_perms = permissions(group=group, obj=obj)

    # XXX could raise FieldDoesNotExist
    if not getattr(group_perms, perm):
        setattr(group_perms, perm, True)
        group_perms.save()

        granted.send(sender=group, perm=perm, object=obj)


def set_user_perms(user, perms, obj):
    """
    Set User permissions to exactly the specified permissions.
    """    
    if perms:
        model = obj.__class__
        permissions = permission_map[model]
        
        all_perms = dict((p, False) for p in get_model_perms(model))
        for perm in perms:
            all_perms[perm] = True
        
        try:
            user_perms = permissions.objects.get(user=user, obj=obj)
        except permissions.DoesNotExist:
            user_perms = permissions(user=user, obj=obj)
        
        for perm, enabled in all_perms.iteritems():
            if enabled and not getattr(user_perms, perm):
                granted.send(sender=user, perm=perm, object=obj)
            elif not enabled and getattr(user_perms, perm):
                revoked.send(sender=user, perm=perm, object=obj)
            setattr(user_perms, perm, enabled)
        
        user_perms.save()
    
    else:
        # removing all perms.
        revoke_all(user, obj)

    return perms


def set_group_perms(group, perms, obj):
    """
    Set group permissions to exactly the specified permissions.
    """
    if perms:
        model = obj.__class__
        permissions = permission_map[model]
        all_perms = dict((p, False) for p in get_model_perms(model))
        for perm in perms:
            all_perms[perm] = True
    
        try:
            group_perms = permissions.objects.get(group=group, obj=obj)
        except permissions.DoesNotExist:
            group_perms = permissions(group=group, obj=obj)
    
        for perm, enabled in all_perms.iteritems():
            if enabled and not getattr(group_perms, perm):
                granted.send(sender=group, perm=perm, object=obj)
            elif not enabled and getattr(group_perms, perm):
                revoked.send(sender=group, perm=perm, object=obj)
    
            setattr(group_perms, perm, enabled)
    
        group_perms.save()

    else:
        # removing all perms.
        revoke_all_group(group, obj)

    return perms


def revoke(user, perm, obj):
    """
    Revoke a permission from a User.
    """

    model = obj.__class__
    permissions = permission_map[model]

    try:
        user_perms = permissions.objects.get(user=user, obj=obj)

        if getattr(user_perms, perm):
            revoked.send(sender=user, perm=perm, object=obj)

            setattr(user_perms, perm, False)

            # If any permissions remain, save the model. Otherwise, remove it
            # from the table.
            if any(getattr(user_perms, p)
                    for p in get_model_perms(model)):
                user_perms.save()
            else:
                user_perms.delete()

    except ObjectDoesNotExist:
        # User didnt have permission to begin with; do nothing.
        pass


def revoke_group(group, perm, obj):
    """
    Revokes a permission from a Group.
    """

    model = obj.__class__
    permissions = permission_map[model]

    try:
        group_perms = permissions.objects.get(group=group, obj=obj)

        if getattr(group_perms, perm):
            revoked.send(sender=group, perm=perm, object=obj)

            setattr(group_perms, perm, False)

            # If any permissions remain, save the model. Otherwise, remove it
            # from the table.
            if any(getattr(group_perms, p)
                    for p in get_model_perms(model)):
                group_perms.save()
            else:
                group_perms.delete()

    except ObjectDoesNotExist:
        # Group didnt have permission to begin with; do nothing.
        pass


def revoke_all(user, obj):
    """
    Revoke all permissions from a User.
    """

    model = obj.__class__
    permissions = permission_map[model]

    try:
        user_perms = permissions.objects.get(user=user, obj=obj)

        for perm in get_model_perms(model):
            if getattr(user_perms, perm):
                revoked.send(sender=user, perm=perm, object=obj)

        user_perms.delete()
    except ObjectDoesNotExist:
        pass


def revoke_all_group(group, obj):
    """
    Revoke all permissions from a Group.
    """

    model = obj.__class__
    permissions = permission_map[model]

    try:
        group_perms = permissions.objects.get(group=group, obj=obj)

        for perm in get_model_perms(model):
            if getattr(group_perms, perm):
                revoked.send(sender=group, perm=perm, object=obj)

        group_perms.delete()
    except ObjectDoesNotExist:
        pass


def get_user_perms(user, obj):
    """
    Return the permissions that the User has on the given object.
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
    Return the permissions that the Group has on the given object.
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
    Return all available permissions for a model.

    This function accepts both Models and model instances.
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


def user_has_perm(user, perm, obj, groups=True):
    """
    Check if a User has a permission on a given object.

    If groups is True, the permissions of all Groups containing the user
    will also be considered.

    Silently returns False in case of several errors:

     * The model is not registered for permissions
     * The permission does not exist on this model
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
            .filter(Q(user=user) | Q(group__user=user)) \
            .exists()
    else:
        return permissions.objects.filter(user=user, obj=obj, **d).exists()


def group_has_perm(group, perm, obj):
    """
    Check if a Group has a permission on a given object.

    Silently returns False in case of several errors:

     * The model is not registered for permissions
     * The permission does not exist on this model
    """

    model = obj.__class__
    try:
        permissions = permission_map[model]
    except KeyError:
        return False

    if perm not in get_model_perms(model):
        # not a valid permission
        return False

    d = {
            perm: True,
    }

    return permissions.objects.filter(group=group, obj=obj, **d).exists()


def user_has_any_perms(user, obj, perms=None, groups=True, **related):
    """
    Check whether the User has *any* permission on the given object.
    """
    instance = isinstance(obj, (Model,))
    model = obj.__class__ if instance else obj
    name = model.__name__
    try:
        permissions = permission_map[model]
    except KeyError:
        return False

    # XXX when performing related query for has_any, start with the group
    # table, this allows us to join the different model tables together
    if related:
        # start clause by matching group
        q = Q(**{'%s_uperms__user' % name:user})
        
        # optionally filter by instance
        if instance:
            q &= Q(**{'%s_uperms__obj' % name:obj})
        
        # optionally add perms
        if perms:
            # create Q clauses out of perms and OR them all together
            table = '%s_uperms__%%s' % name
            q &= reduce(or_, (Q(**{table % perm:True}) for perm in perms))
        
        # optionally add groups
        if groups:
            clause = Q(**{'groups__%s_gperms__obj'%name:obj})
            #optionally add perms
            if perms:
                perm_table = 'groups__%s_gperms__%%s' % name
                clause &= reduce(or_, (Q(**{perm_table % perm:True}) for perm in perms))
            q |= clause
        
        # add related models - has any queries the related name is a Class name
        # with an optional path appended at the end.  The Class is used to join
        # against the additional perm table, and optionally through to the
        # original item.
        for field, perms in related.items():
            field, chaff, path = field.partition('__')
            
            # start clause by matching user
            clause = Q(**{'%s_uperms__user'%field:user})
            
            if instance:
                # optionally join object using supplied path
                if path != '':
                    clause &= Q(**{'%s_uperms__obj__%s'%(field, path):obj})
                else:
                    # we must have a path to map this class to the related instance
                    raise InvalidQueryException('has_any requires query paths for related models when checking permissions on a specific instance')
            
            # optionally add perms
            if perms:
                # create Q clauses out of perms and OR them all together
                perm_table = '%s_uperms__%%s' % field
                clause &= reduce(or_, (Q(**{perm_table % perm:True}) for perm in perms))
            
            # optionally add groups
            if groups:
                group_clause = Q(**{'groups__%s_gperms__obj__%s'%(field, path):obj})
                    
                #optionally add perms (group)
                if perms:
                    perm_table = 'groups__%s_gperms__%%s' % field
                    group_clause &= reduce(or_, (Q(**{perm_table % perm:True}) for perm in perms))
                clause |= group_clause
            
            q |= clause
        
        #print (User.objects.filter(q).query)
        
        return User.objects.filter(q).exists()

    else:
        # standard query - query the perms table directly to avoid joins
        # create perm clause, or implicit any
        
        # start query with group
        q = Q(user=user)
        
        # optionally add groups
        if groups:
            q |= Q(group__user=user)
        
        # optionally filter by instance
        if instance:
            q &= Q(obj=obj)
        
        # optionally add perms
        if perms:
            # create Q clauses out of perms and OR them all together
            q &= reduce(or_, (Q(**{perm:True}) for perm in perms))
        
        # select model or instance level query
        return permissions.objects.filter(q).exists()


def group_has_any_perms(group, obj, perms=None, **related):
    """
    Check whether the Group has *any* permission on the given object.
    """
    instance = isinstance(obj, (Model,))
    model = obj.__class__ if instance else obj
    name = model.__name__
    try:
        permissions = permission_map[model]
    except KeyError:
        return False

    # XXX when performing related query for has_any, start with the group
    # table, this allows us to join the different model tables together
    if related:
        # start clause by matching group
        q = Q(**{'%s_gperms__group' % name:group})
        
        # optionally filter by instance
        if instance:
            q &= Q(**{'%s_gperms__obj'%name:obj})
        
        # optionally add perms
        if perms:
            # create Q clauses out of perms and OR them all together
            table = '%s_gperms__%%s' % name
            q &= reduce(or_, (Q(**{table % perm:True}) for perm in perms))
        
        # add related models - has any queries the related name is a Class name
        # with an optional path appended at the end.  The Class is used to join
        # against the additional perm table, and optionally through to the
        # original item.
        for field, perms in related.items():
            field, chaff, path = field.partition('__')
            table = '%s_gperms' % field
            
            # start clause by matching group
            clause = Q(**{'%s__group' % table:group})
            
            if instance:
                # optionally join object using supplied path
                if path != '':
                    clause &= Q(**{'%s__obj__%s'%(table, path):obj})
                else:
                    # we must have a path to map this class to the related instance
                    raise InvalidQueryException('has_any requires query paths for related models when checking permissions on a specific instance')
            
            # optionally add perms
            if perms:
                # create Q clauses out of perms and OR them all together
                table = '%s__%%s' % table
                clause &= reduce(or_, (Q(**{table % perm:True}) for perm in perms))
            
            q |= clause
        
        return Group.objects.filter(q).exists()

    else:
        # standard query - query the perms table directly to avoid joins
        # create perm clause, or implicit any
        
        # start query with group
        q = Q(group=group)
        
        # optionally filter by instance
        if instance:
            q &= Q(obj=obj)
        
        # optionally add perms
        if perms:
            # create Q clauses out of perms and OR them all together
            q &= reduce(or_, (Q(**{perm:True}) for perm in perms))
        
        # select model or instance level query
        return permissions.objects.filter(q).exists()


def user_has_all_perms(user, obj, perms, groups=True, **related):
    """
    Check whether the User has *all* permission on the given object.
    """
    instance = isinstance(obj, (Model,))
    model = obj.__class__ if instance else obj
    name = model.__name__
    try:
        permissions = permission_map[model]
    except KeyError:
        return False
    
    # related fields are built as sub-clauses for each related field.  To follow
    # the relation we must add a clause that follows the relationship path from
    # the object to its related models.  We must also join on the user to the
    # resulting permissions table so that the user rows are matched.
    if related:
        
        # base matches object
        q = Q(pk=user.pk)
        
        # create base query requiring all permissions
        # optionally match instance
        uperm_clause = {'%s_uperms__obj'%name:obj} if instance else {}
        for perm in perms:
            table = '%s_uperms__%%s' % name
            uperm_clause[table%perm] = True
        
        # optionally check groups
        if groups:
            table = 'groups__%s_gperms__%%s' % name
            gperm_clause = {'groups__%s_gperms__obj' % name: obj} if instance else {}
            for perm in perms:
                gperm_clause[table % perm] = True
            q &= (Q(**gperm_clause) | Q(**uperm_clause))
        else:
            q &= Q(**uperm_clause)
        
        # optionally add related fields
        for field, perms in related.items():
            field, chaff, path = field.partition('__')
            
            if path == '':
                # we must have a path to map this class to the related instance
                raise InvalidQueryException('has_all requires query paths for related models')
            
            # build base clause off object
            if instance:
                clause = {'%s_uperms__obj__%s'%(field, path):obj}
            else:
                clause = {'%s_uperms__obj'%name:F('%s_uperms__obj__%s'%(field, path))}
            
            # add all perms
            table = '%s_uperms__%%s' % field
            for perm in perms:
                clause[table % perm] = True
            uperm_clause = Q(**clause)
            
            # optionally add groups
            if groups:
                table = 'groups__%s_gperms__%%s' % field
                if instance:
                    gperm_clause = {'groups__%s_gperms__obj' % field: obj}
                else:
                    gperm_clause = {'%s_uperms__obj'%name:F('groups__%s_gperms__obj__%s'%(field, path))}
                for perm in perms:
                    gperm_clause[table % perm] = True
                q |= (Q(**gperm_clause) | uperm_clause)
            else:
                q &= uperm_clause
            
            
        #print '-----'
        #print str(User.objects.filter(q).query)
        return User.objects.filter(q).exists()

    else:
        # base matches object
        q = Q(user=user)
        
        # optionally check groups
        if groups:
            q |= Q(group__user=user)
        
        # base query matches object
        if instance:
            q &= Q(obj=obj)
        
        # create base query requiring all permissions
        perm_clauses = {}
        for perm in perms:
            perm_clauses[perm] = True
        q &= Q(**perm_clauses)
        
        return permissions.objects.filter(q).exists()


def group_has_all_perms(group, obj, perms, **related):
    """
    Check whether the Group has *all* permission on the given object.
    
    @param group - group for which to check permissions
    @param obj - Model or Instance for which to check permissions on.
    @param perms - list of permissions that must be matched
    
    @return True if group has all permissions on an instance.  If a model class
    is given this returns True if the group has permissions on any instance of
    the model.
    """
    instance = isinstance(obj, (Model,))
    model = obj.__class__ if instance else obj
    name = model.__name__
    try:
        permissions = permission_map[model]
    except KeyError:
        return False
    
    # related fields are built as sub-clauses for each related field.  To follow
    # the relation we must add a clause that follows the relationship path from
    # the object to its related models.  We must also join on the user to the
    # resulting permissions table so that the user rows are matched.
    if related:
        
        # start clause by matching group
        q = Q(**{'%s_gperms__group' % name:group})
        
        # optionally filter by instance
        if instance:
            q &= Q(**{'%s_gperms__obj' % name:obj})
        
        # add perms
        table = '%s_gperms__%%s' % name
        perm_clause = {}
        for perm in perms:
            perm_clause[table % perm] = True
        q &= Q(**perm_clause)
        
        for field, perms in related.items():
            field, chaff, path = field.partition('__')
            
            # add group
            q &= Q(**{'%s_gperms__group' % field:group})
            
            if instance:
                # optionally join object using supplied path
                if path != '':
                    q &= Q(**{'%s_gperms__obj__%s'%(field, path):obj})
                else:
                    # we must have a path to map this class to the related instance
                    raise InvalidQueryException('has_any requires query paths for related models when checking permissions on a specific instance')
            
            # add all perms
            table = '%s_gperms__%%s' % field
            perm_clause = {}
            for perm in perms:
                perm_clause[table % perm] = True
            q &= Q(**perm_clause)
            
        return Group.objects.filter(q).exists()
    
    else:
        # base matches object
        q = Q(group=group)
        
        # base query matches object
        if instance:
            q &= Q(obj=obj)
        
        # create base query requiring all permissions
        perm_clauses = {}
        for perm in perms:
            perm_clauses[perm] = True
        q &= Q(**perm_clauses)
        
        return permissions.objects.filter(q).exists()


def get_users_any(obj, perms=None, groups=True):
    """
    Retrieve the list of Users that have any of the permissions on the given
    object.

    @param perms - perms to check, or None if match *any* perms
    @param groups - include users with permissions via groups
    """
    model = obj.__class__
    permissions = permission_map[model]

    perm_table = "%s_uperms__%%s" % model.__name__
    obj_table = "%s_uperms__obj" % model.__name__
    d = {
            obj_table: obj,
    }

    if perms:
        # create Q clauses out of perms and OR them all together
        q = reduce(or_, (Q(**{perm_table % perm:True}) for perm in perms))
        
        if groups:
            # handle groups by checking perms for any group users are in.
            #
            # Do this by creating separate user and group clauses that check
            # the right object with the right set of perms.  Combine the clauses
            # together like so:
            #     (obj AND perms) OR (group_obj AND group perms)
            
            group_perm_table = "groups__%s_gperms__%%s" % model.__name__
            group_obj_table = "groups__%s_gperms__obj" % model.__name__
            gperms = reduce(or_, (Q(**{group_perm_table % perm:True}) \
                                  for perm in perms))
            group_clause = Q(**{group_obj_table:obj}) & gperms
            return User.objects.filter((Q(**d) & q) | group_clause).distinct()
            
        return User.objects.filter(q, **d).distinct()
    
    if groups:
        # handle groups with *any* perm by adding a clause that checks for the
        # object via the groups table.  this give inherent group membership
        # check.
        group_obj_table = "groups__%s_gperms__obj" % model.__name__
        group_clause = Q(**{group_obj_table:obj})
        return User.objects.filter(Q(**d) | group_clause).distinct()
    
    return User.objects.filter(**d).distinct()


def get_users_any(obj, perms=None, groups=True, **related):
    """
    Retrieve the list of Users that have any of the permissions on the given
    object.

    @param perms - perms to check, or None if match *any* perms
    @param groups - include users with permissions via groups
    """
    model = obj.__class__
    name = model.__name__
    try:
        permissions = permission_map[model]
    except KeyError:
        return False

    # start by filtering instance
    q = Q(**{'%s_uperms__obj' % name:obj})
    
    # optionally add perms
    if perms:
        # create Q clauses out of perms and OR them all together
        table = '%s_uperms__%%s' % name
        q &= reduce(or_, (Q(**{table % perm:True}) for perm in perms))
    
    # optionally add groups
    if groups:
        clause = Q(**{'groups__%s_gperms__obj'%name:obj})
        #optionally add perms
        if perms:
            perm_table = 'groups__%s_gperms__%%s' % name
            clause &= reduce(or_, (Q(**{perm_table % perm:True}) for perm in perms))
        q |= clause
        
    # add related models - has any queries the related name is a Class name
    # with an optional path appended at the end.  The Class is used to join
    # against the additional perm table, and optionally through to the
    # original item.
    if related:
        for field, perms in related.items():
            field, chaff, path = field.partition('__')
            
            # start clause by instance
            # we must have a path to map this class to the related instance
            if path == '':
                raise InvalidQueryException('has_any requires query paths for related models when checking permissions on a specific instance')
            clause = Q(**{'%s_uperms__obj__%s'%(field, path):obj})
            
            # optionally add perms
            if perms:
                # create Q clauses out of perms and OR them all together
                perm_table = '%s_uperms__%%s' % field
                clause &= reduce(or_, (Q(**{perm_table % perm:True}) for perm in perms))
            
            # optionally add groups
            if groups:
                group_clause = Q(**{'groups__%s_gperms__obj__%s'%(field, path):obj})
                #optionally add perms (group)
                if perms:
                    perm_table = 'groups__%s_gperms__%%s' % field
                    group_clause &= reduce(or_, (Q(**{perm_table % perm:True}) for perm in perms))
                clause |= group_clause
            
            q |= clause
    
    #print str(User.objects.filter(q).distinct().query)
    
    return User.objects.filter(q).distinct()


def get_users_all(obj, perms, groups=True, **related):
    """
    Retrieve the list of Users that have all of the permissions on the given
    object.

    @param perms - perms to check
    @param groups - include users with permissions via groups
    """
    model = obj.__class__
    name = model.__name__
    permissions = permission_map[model]
    
    # create base query requiring all permissions
    perm_clauses = {'%s_uperms__obj'%name:obj}
    for perm in perms:
        table = '%s_uperms__%%s' % name
        perm_clauses[table%perm] = True
    q = Q(**perm_clauses)
    
    # optionally check groups
    if groups:
        table = 'groups__%s_gperms__%%s' % name
        perm_clauses = {'groups__%s_gperms__obj' % name: obj}
        for perm in perms:
            perm_clauses[table % perm] = True
        q |= Q(**perm_clauses)

    # related fields are built as sub-clauses for each related field.  To follow
    # the relation we must add a clause that follows the relationship path from
    # the object to its related models.  We must also join on the user to the
    # resulting permissions table so that the user rows are matched.
    if related:
        # optionally add related fields
        for field, perms in related.items():
            field, chaff, path = field.partition('__')
            table = '%s_uperms' % field
            
            # build base clause off object
            if path == '':
                # we must have a path to map this class to the related instance
                raise InvalidQueryException('has_any requires query paths for related models when checking permissions on a specific instance')
            
            # add all perms
            perm_table = '%s__%%s' % table
            perm_clauses = {'%s__obj__%s'%(table, path):obj}
            for perm in perms:
                perm_clauses[perm_table % perm] = True
            clause = Q(**perm_clauses)
            
            # optionally add groups
            if groups:
                table = 'groups__%s_gperms__%%s' % field
                perm_clauses = {'groups__%s_gperms__obj__%s' % (field, path): obj}
                for perm in perms:
                    perm_clauses[table % perm] = True
                clause |= Q(**perm_clauses)
            
            q &= clause

    # return users filted by intricate Q statement
    return User.objects.filter(q).distinct()


def get_users(obj, groups=True):
    """
    Retrieve the list of Users that have permissions on the given object.
    """
    
    return get_users_any(obj)


def get_groups_any(obj, perms=None, **related):
    """
    Retrieve the list of Groups that have any of the permissions on the given
    object.

    @param perms - perms to check, or None to check for *any* perms
    """
    
    instance = isinstance(obj, (Model,))
    model = obj.__class__ if instance else obj
    name = model.__name__
    try:
        permissions = permission_map[model]
    except KeyError:
        return False

    q = Q(**{'%s_gperms__obj'%name:obj})
    
    # optionally add perms
    if perms:
        # create Q clauses out of perms and OR them all together
        table = '%s_gperms__%%s' % name
        q &= reduce(or_, (Q(**{table % perm:True}) for perm in perms))
        
    
    for field, perms in related.items():
        field, chaff, path = field.partition('__')
        table = '%s_gperms' % field
        
        # build base clause off object
        if path == '':
            # we must have a path to map this class to the related instance
            raise InvalidQueryException('has_any requires query paths for related models when checking permissions on a specific instance')
        clause = Q(**{'%s__obj__%s'%(table, path):obj})
        
        # optionally add perms
        if perms:
            # create Q clauses out of perms and OR them all together
            perm_table = '%s__%%s' % table
            clause &= reduce(or_, (Q(**{perm_table % perm:True}) for perm in perms))
        
        q |= clause
    
    return Group.objects.filter(q).distinct()


def get_groups_all(obj, perms, **related):
    """
    Retrieve the list of Groups that have all of the permissions on the given
    object.

    @param perms - perms to check
    """
    instance = isinstance(obj, (Model,))
    model = obj.__class__ if instance else obj
    name = model.__name__
    try:
        permissions = permission_map[model]
    except KeyError:
        return False

    # build main clause out of object and perms
    clause = {'%s_gperms__obj'%name:obj}
    perm_table = '%s_gperms__%%s' % name
    for perm in perms:
        clause[perm_table % perm] = True
    q = Q(**clause)
    
    # related fields are built as sub-clauses for each related field.  To follow
    # the relation we must add a clause that follows the relationship path from
    # the object to its related models.  We must also join on the group to the
    # resulting permissions table so that the group rows are matched.
    for field, perms in related.items():
        field, chaff, path = field.partition('__')
        table = '%s_gperms' % field
        
        # build base clause off object
        if path == '':
            # we must have a path to map this class to the related instance
            raise InvalidQueryException('has_any requires query paths for related models when checking permissions on a specific instance')
        clause = {'%s__obj__%s'%(table, path):obj}
        
        # add perms to clause
        perm_table = '%s__%%s' % table
        for perm in perms:
            clause[perm_table % perm] = True
        
        # add related clause to main clause
        q &= Q(**clause)
    
    return Group.objects.filter(q).distinct()


def get_groups(obj):
    """
    Retrieve the list of Users that have permissions on the given object.
    """

    return get_groups_any(obj)


def perms_on_any(user, model, perms, groups=True):
    """
    Determine whether the user has any of the listed permissions on any instances of
    the Model.

    This function checks whether either user permissions or group permissions
    are set, inclusively, using logical OR.

    @param user: user who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @return true if has perms on any instance of model
    
    @deprecated - replaced by user_has_any_perms()
    """
    warn('user.perms_on_any() deprecated in lieu of user.has_any_perms()', stacklevel=2)
    return user_has_any_perms(user, model, perms, groups)


def filter_on_perms(user, model, perms, groups=True):
    warn('user.filter_on_perms() deprecated in lieu of user.get_objects_any_perms()', stacklevel=2)
    return user_get_objects_any_perms(user, model, perms, groups)


def user_get_objects_any_perms(user, model, perms=None, groups=True, **related):
    """
    Make a filtered QuerySet of objects for which the User has any of the
    requested permissions, optionally including permissions inherited from
    Groups.

    @param user: user who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @param groups: include perms the user has from membership in Groups
    @param related: kwargs for related models.  Each kwarg name should be a
    valid query argument, you may follow as many tables as you like and perms
    are optional  E.g. foo__bar=['xoo'], foo=None
    @return a queryset of matching objects
    """
    
    q = Q(operms__user=user)

    # optionally add groups
    if groups:
        q |= Q(operms__group__user=user)
    
    # optionally add specific perms
    if perms:
        # OR all user permission clauses together
        model_perms = get_model_perms(model)
        perm_clause = reduce(or_, (Q(**{"operms__%s" % perm: True}) \
                                   for perm in perms if perm in model_perms))
        q &= perm_clause

    # related fields are built as sub-clauses for each related field.  To follow
    # the relation we must add a clause that follows the relationship path to
    # the operms table for that model, and optionally include perms.
    if related:
        
        for field in related:
            # build user clause that follows relationship through operms to user
            clause = Q(**{'%s__operms__user'%field:user})
            perms = related[field]
            
            # optionally include groups
            if groups:
                clause |= Q(**{'%s__operms__group__user'%field:user})
            
            # optionally include specific perms.
            if perms:
                perm_field = '%s__operms__%%s' % field
                perm_clause = reduce(or_, (Q(**{perm_field % perm: True}) \
                                                for perm in perms))
                clause &= perm_clause
            
            #add finished query
            q |= clause

    # return objects query filtered by the intricate Q statement
    return model.objects.filter(q).distinct()


def group_get_objects_any_perms(group, model, perms=None, **related):
    """
    Make a filtered QuerySet of objects for which the Group has any of the 
    requested permissions.

    @param group: group who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @param groups: include perms the user has from membership in Groups
    @return a queryset of matching objects
    """

    # base clause matches group
    q = Q(operms__group=group)

    # optionally add permissions
    if perms:
        # permissions specified, OR all user permission clauses together
        model_perms = get_model_perms(model)
        perm_clause = reduce(or_, (Q(**{"operms__%s" % perm: True}) \
                                   for perm in perms if perm in model_perms))
        q &= perm_clause
    
    # related fields are built as sub-clauses for each related field.  To follow
    # the relation we must add a clause that follows the relationship path to
    # the operms table for that model, and optionally include perms.
    if related:
        for field, perms in related.items():
            # build group clause that follows relationship
            clause = Q(**{'%s__operms__group'%field:group})
            
            # optionally include specific perms.
            if perms:
                perm_field = '%s__operms__%%s' % field
                perm_clause = reduce(or_, (Q(**{perm_field % perm: True}) \
                                                for perm in perms))
                clause &= perm_clause
            
            #add finished query
            q |= clause
    
    return model.objects.filter(q).distinct()


def user_get_objects_all_perms(user, model, perms, groups=True, **related):
    """
    Make a filtered QuerySet of objects for which the User has all requested
    permissions, optionally including permissions inherited from Groups.

    @param user: user who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @param groups: include perms the user has from membership in Groups
    @return a queryset of matching objects
    """
    
    # create kwargs including all perms that must be matched
    perm_clause = {}
    for perm in perms:
        perm_clause['operms__%s' % perm] = True
    
    if groups:
        # must match either a user or group clause + one of the perm clauses
        user_clause = Q(operms__group__user=user) | Q(operms__user=user)
        q = user_clause & Q(**perm_clause)
    
    else:
        # must match user clause + all of the perm clauses
        q = Q(operms__user=user, **perm_clause)

    # related fields are built as sub-clauses for each related field.  To follow
    # the relation we must add a clause that follows the relationship path to
    # the operms table for that model, and optionally include perms.
    if related:
        
        for field in related:
            # build user clause that follows relationship through operms to user
            clause = Q(**{'%s__operms__user'%field:user})
            perms = related[field]
            
            # optionally include groups
            if groups:
                clause |= Q(**{'%s__operms__group__user'%field:user})
            
            # create kwargs including all perms that must be matched
            perm_clause = {}
            for perm in perms:
                perm_clause['operms__%s' % perm] = True
            clause &= Q(**perm_clause)
            
            #add finished query
            q &= clause

    # return objects query filtered by the intricate Q statement
    return model.objects.filter(q).distinct()


def group_get_objects_all_perms(group, model, perms, **related):
    """
    Make a filtered QuerySet of objects for which the User has all requested
    permissions, optionally including permissions inherited from Groups.

    @param group: group who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @param groups: include perms the user has from membership in Groups
    @return a queryset of matching objects
    """

    # base clause matches group
    q = Q(operms__group=group)

    # create kwargs including all perms that must be matched
    perm_clause = {}
    for perm in perms:
        perm_clause['operms__%s' % perm] = True
    q &= Q(**perm_clause)
    
    # related fields are built as sub-clauses for each related field.  To follow
    # the relation we must add a clause that follows the relationship path to
    # the operms table for that model, and optionally include perms.
    if related:
        for field, perms in related.items():
            # build group clause that follows relationship
            q &= Q(**{'%s__operms__group'%field:group})
            
            # create kwargs including all perms that must be matched
            perm_clause = {}
            for perm in perms:
                perm_clause['operms__%s' % perm] = True
            q &= Q(**perm_clause)
    
    return model.objects.filter(q).distinct()


def user_get_all_objects_any_perms(user, groups=True):
    """
    Get all objects from all registered models that the user has any permission
    for.
    
    This method does not accept a list of permissions since in most cases
    permissions will not exist across all models.  If a permission didn't exist
    on any model then it would cause an error to be thrown.
    
    @param user - user to check perms for
    @param groups - include permissions through groups
    @return a dictionary mapping class to a queryset of objects
    """
    perms = {}
    for cls in permission_map:
        perms[cls] = user_get_objects_any_perms(user, cls, groups=groups)
    return perms


def group_get_all_objects_any_perms(group):
    """
    Get all objects from all registered models that the group has any permission
    for.
    
    This method does not accept a list of permissions since in most cases
    permissions will not exist across all models.  If a permission didn't exist
    on any model then it would cause an error to be thrown.
    
    @param group - group to check perms for
    @return a dictionary mapping class to a queryset of objects
    """
    perms = {}
    for cls in permission_map:
        perms[cls] = group_get_objects_any_perms(group, cls)
    return perms


def filter_on_group_perms(group, model, perms):
    """
    Make a filtered QuerySet of objects for which the Group has any
    permissions.

    @param usergroup: Group who must have permissions
    @param model: model on which to filter
    @param perms: list of perms to match
    @param clauses: additional clauses to be added to the queryset
    @return a queryset of matching objects
    """
    warn('group.filter_on_perms() deprecated in lieu of group.get_objects_any_perms()', stacklevel=2)
    return group_get_objects_any_perms(group, model, perms)


# make some methods available as bound methods
setattr(User, 'grant', grant)
setattr(User, 'revoke', revoke)
setattr(User, 'revoke_all', revoke_all)
setattr(User, 'has_object_perm', user_has_perm)
setattr(User, 'has_any_perms', user_has_any_perms)
setattr(User, 'has_all_perms', user_has_all_perms)
setattr(User, 'get_perms', get_user_perms)
setattr(User, 'set_perms', set_user_perms)
setattr(User, 'get_objects_any_perms', user_get_objects_any_perms)
setattr(User, 'get_objects_all_perms', user_get_objects_all_perms)
setattr(User, 'get_all_objects_any_perms', user_get_all_objects_any_perms)

# deprecated
setattr(User, 'filter_on_perms', filter_on_perms)
setattr(User, 'perms_on_any', perms_on_any)

setattr(Group, 'grant', grant_group)
setattr(Group, 'revoke', revoke_group)
setattr(Group, 'revoke_all', revoke_all_group)
setattr(Group, 'has_perm', group_has_perm)
setattr(Group, 'has_any_perms', group_has_any_perms)
setattr(Group, 'has_all_perms', group_has_all_perms)
setattr(Group, 'get_perms', get_group_perms)
setattr(Group, 'set_perms', set_group_perms)
setattr(Group, 'get_objects_any_perms', group_get_objects_any_perms)
setattr(Group, 'get_objects_all_perms', group_get_objects_all_perms)
setattr(Group, 'get_all_objects_any_perms', group_get_all_objects_any_perms)

# deprecated
setattr(Group, 'filter_on_perms', filter_on_group_perms)
