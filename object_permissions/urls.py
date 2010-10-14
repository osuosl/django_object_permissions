import os

from django.conf.urls.defaults import *

urlpatterns = patterns('ganeti_webmgr.object_permissions.views.user_groups',
    # UserGroups
    url(r'^user_groups/$', 'list', name="user_group-list"),
    url(r'^user_group/?$', 'detail', name="user_group-add"),
    url(r'^user_group/(?P<id>\d+)/?$', 'detail', name="user_group-detail"),
    url(r'^user_group/(?P<id>\d+)/user/add/?$','add_user', name="user_group-add-user"),
    url(r'^user_group/(?P<id>\d+)/user/remove/?$','remove_user', name="user_group-remove-user"),
    url(r'^user_group/(?P<id>\d+)/user/$','user_permissions', name="user_group-user-permissions"),
)

#The following is used to serve up local media files like images
root = '%s/media' % os.path.dirname(os.path.realpath(__file__))
urlpatterns += patterns('',
    (r'^object_permissions_media/(?P<path>.*)', 'django.views.static.serve',\
     {'document_root':  root}),
)