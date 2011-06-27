from django.contrib.auth.models import User
from django.template import Library

from object_permissions.models import Group
from object_permissions.registration import get_user_perms, get_users_all

register = Library()


@register.filter
def permissions(user, object):
    """
    Returns the list of permissions a user has on an object
    """
    if user:
        return user.get_perms(object, False)
    return []


@register.filter
def group_admin(user, group=None):
    """
    Returns True or False based on if the user is an admin for any Groups
    """
    if group:
        return user.is_superuser or user.has_perm(group, 'admin')

    return user.is_superuser or user.has_any_perms(Group, ['admin'])


@register.filter
def class_name(cls):
    """
    Returns name of class for a class object
    """
    return cls.__name__


@register.filter
def is_user(obj):
    """
    Returns True if obj is a user
    """
    return isinstance(obj, (User,))


@register.simple_tag
def number_group_admins(group):
    "Return number of users with admin perms for specified group"
    return get_users_all(group, ["admin",], False).count()


@register.simple_tag
def permalink(obj, display=None):
    """
    Return a link for an object if it as a get_absolute_url method.  Not all
    models will have this.  Models that do not have the method will be rendered
    as text
    """
    display = display if display else obj
    if hasattr(obj, 'get_absolute_url'):
        return '<a href="%s">%s</a>' % (obj.get_absolute_url(), display)
    else:
        return obj