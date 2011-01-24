import os

from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('object_permissions.views.groups',
    # Groups
    url(r'^groups/$', 'list', name="usergroup-list"),
    url(r'^group/?$', 'detail', name="usergroup"),
    url(r'^group/(?P<id>\d+)/?$', 'detail', name="usergroup-detail"),
    url(r'^group/(?P<id>\d+)/user/add/?$','add_user', name="usergroup-add-user"),
    url(r'^group/(?P<id>\d+)/user/remove/?$','remove_user', name="usergroup-remove-user"),
    url(r'^group/(?P<id>\d+)/permissions/?$','user_permissions', name="usergroup-permissions"),
    url(r'^group/(?P<id>\d+)/permissions/user/(?P<user_id>\d+)/?$','user_permissions', name="group-user-permissions"),
    url(r'^group/(?P<id>\d+)/permissions/all/?$','all_permissions', name="group-all-permissions"),
)

urlpatterns += patterns('object_permissions.views.permissions',
    # Users
    url(r'^user/(?P<id>\d+)/permissions/all/?$','all_permissions', name="user-all-permissions"),
)

#The following is used to serve up local media files like images
root = '%s/media' % os.path.dirname(os.path.realpath(__file__))
urlpatterns += patterns('',
    (r'^object_permissions_media/(?P<path>.*)', 'django.views.static.serve',\
     {'document_root':  root}),
)
