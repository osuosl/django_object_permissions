import django.dispatch

granted = django.dispatch.Signal(providing_args=["perm", "object"])
revoked = django.dispatch.Signal(providing_args=["perm", "object"])


# signals issues when a user has edited permissions or groups via a view
# provided by object permissions.  These signals differ from granted and revoked
# because they require the user (editor) that was editing the permissions.
#
# granted and revoked signals will still be sent if permissions are edited

# sent when a user has been added to a group
view_add_user = django.dispatch.Signal(providing_args=["editor", "user", "obj"])

# sent when a user has been remove from a group
view_remove_user = django.dispatch.Signal(providing_args=["editor", "user", "obj"])

# send when a user's permissions have been edited
view_edit_user = django.dispatch.Signal(providing_args=["editor", "user", "obj"])