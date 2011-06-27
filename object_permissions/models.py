from django.contrib.auth.models import Group

from object_permissions import register

# register internal perms
GROUP_PARAMS = {
    'perms':{
        'admin':{
            'label':'Admin',
            'description':'Can add or remove users, and edit their permissions for the group'
        }
    }
}

register(GROUP_PARAMS, Group, 'object_permissions')