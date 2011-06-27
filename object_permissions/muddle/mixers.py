from muddle.shots import register, TemplateMixer

# permissions
register('user-detail-tab', TemplateMixer('object_permissions/muddle/user_permissions.html'))
register('group-detail-tab', TemplateMixer('object_permissions/muddle/group_permissions.html'))

# group list
register('group-list-table-headers', TemplateMixer('object_permissions/muddle/group/group_headers.html'))
register('group-list-table-cells', TemplateMixer('object_permissions/muddle/group/group_row.html'))

# group users
register('group-users-table-headers', TemplateMixer('object_permissions/muddle/group/user_headers.html'))
register('group-users-table-cells', TemplateMixer('object_permissions/muddle/group/user_row.html'))