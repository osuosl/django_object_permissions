from django.contrib.auth.models import Group

from object_permissions import register

# register internal perms
register(['admin'], Group)