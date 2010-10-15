import os

from django.conf.urls.defaults import *

urlpatterns = patterns('object_permissions.views.user_groups',
    # UserGroups
    url(r'^user_groups/$', 'list', name="usergroup-list"),
    url(r'^user_group/?$', 'detail', name="usergroup"),
    url(r'^user_group/(?P<id>\d+)/?$', 'detail', name="usergroup-detail"),
    url(r'^user_group/(?P<id>\d+)/user/add/?$','add_user', name="usergroup-add-user"),
    url(r'^user_group/(?P<id>\d+)/user/remove/?$','remove_user', name="usergroup-remove-user"),
    url(r'^user_group/(?P<id>\d+)/permissions/?$','user_permissions', name="usergroup-permissions"),
    url(r'^user_group/(?P<id>\d+)/permissions/user/(?P<user_id>\d+)/?$','user_permissions', name="user_group-user-permissions"),
)

#The following is used to serve up local media files like images
root = '%s/media' % os.path.dirname(os.path.realpath(__file__))
urlpatterns += patterns('',
    (r'^object_permissions_media/(?P<path>.*)', 'django.views.static.serve',\
     {'document_root':  root}),
)