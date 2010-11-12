from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType


class UserGroup(models.Model):
    """
    A UserGroup is used to group people together, and then give them common
    permissions on an object.  This is useful when an organization has many
    users and you want to control access via membership in the organization.
    """
    name = models.CharField(max_length=64, unique=True)
    users = models.ManyToManyField(User, related_name='user_groups',
                                   null=True, blank=True)

    def __unicode__(self):
        return self.name