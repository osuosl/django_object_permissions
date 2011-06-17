import os

from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('object_permissions.views.groups',
    url(r'^group/(?P<id>\d+)/permissions/?$','user_permissions', name="group-permissions"),
    url(r'^group/(?P<id>\d+)/permissions/user/(?P<user_id>\d+)/?$','user_permissions', name="group-user-permissions"),
    url(r'^group/(?P<id>\d+)/permissions/all/?$','all_permissions', name="group-all-permissions"),
)

urlpatterns += patterns('object_permissions.views.permissions',
    # List all perms for a given user
    url(r'^user/(?P<id>\d+)/permissions/all/?$','all_permissions', name="user-all-permissions"),
    
    # add permissions on an object
    url(r'^user/(?P<user_id>\d+)/permissions/(?P<class_name>\w+)/?$','view_obj_permissions', name="user-add-permissions"),
    url(r'^group/(?P<group_id>\d+)/permissions/(?P<class_name>\w+)/?$','view_obj_permissions', name="group-add-permissions"),
    
    # edit permissions on an object
    url(r'^user/(?P<user_id>\d+)/permissions/(?P<class_name>\w+)/(?P<obj_id>\d+)/?$', \
        'view_obj_permissions', name="user-edit-permissions"),
    url(r'^group/(?P<group_id>\d+)/permissions/(?P<class_name>\w+)/(?P<obj_id>\d+)?$', \
        'view_obj_permissions', name="group-edit-permissions"),
)

urlpatterns += patterns('object_permissions.views.widgets',
    url(r'^user/search/?$', 'search_users', name='user-search')
)

#The following is used to serve up local media files like images
root = '%s/media' % os.path.dirname(os.path.realpath(__file__))
urlpatterns += patterns('',
    (r'^object_permissions_media/(?P<path>.*)', 'django.views.static.serve',\
     {'document_root':  root}),
)
