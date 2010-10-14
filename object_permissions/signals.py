import django.dispatch

granted = django.dispatch.Signal(providing_args=["perm", "object"])
revoked = django.dispatch.Signal(providing_args=["perm", "object"])