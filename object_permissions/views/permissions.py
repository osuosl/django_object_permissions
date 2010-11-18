import json

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from object_permissions import get_user_perms, get_group_perms, \
    get_model_perms, grant, revoke, get_users, get_groups
from object_permissions.models import Group


class ObjectPermissionForm(forms.Form):
    """
    Form used for editing permissions
    """
    permissions = forms.MultipleChoiceField(required=False, \
                                            widget=forms.CheckboxSelectMultiple)
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    group = forms.ModelChoiceField(queryset=Group.objects.all(), \
                                   required=False)
    
    def __init__(self, object, *args, **kwargs):
        """
        @param object - the object being granted permissions
        """
        super(ObjectPermissionForm, self).__init__(*args, **kwargs)
        self.object = object
        model_perms = get_model_perms(object)
        self.fields['permissions'].choices = zip(model_perms, model_perms)

    def clean(self):
        """
        validates:
            * mutual exclusivity of user and group
            * a user or group is always selected and set to 'grantee'
        """
        data = self.cleaned_data
        user = data.get('user')
        group = data.get('group')
        if not (user or group) or (user and group):
            raise forms.ValidationError('Choose a group or user')
        
        # add whichever object was selected
        data['grantee'] = user if user else group
        return data
    
    def update_perms(self):
        """
        updates perms for the user based on values passed in
            * grant all perms selected in the form.  Revoke all
            * other available perms that were not selected.
            
        @return list of perms the user now possesses
        """
        perms = self.cleaned_data['permissions']
        grantee = self.cleaned_data['grantee']
        grantee.set_perms(perms, self.object)
        return perms
    

class ObjectPermissionFormNewUsers(ObjectPermissionForm):
    """
    A subclass of permission form that enforces an addtional rule that new users
    must be granted at least one permission.  This is used for objects that
    determine group membership (e.g. listing users with acccess) based on who
    has permissions.
    
    This is different from objects that grant inherent permissions through a
    different membership relationship (e.g. Users in a Group inherit perms)
    """
    
    def clean(self):
        data = super(ObjectPermissionFormNewUsers, self).clean()
        
        if 'grantee' in data:
            grantee = data['grantee']
            perms = data['permissions']
            
            # if grantee does not have permissions, then this is a new user:
            #    - permissions must be selected
            if not grantee.get_perms(self.object) and not perms:
                msg = """You must grant at least 1 permission for new users and groups"""
                self._errors["permissions"] = self.error_class([msg])
        
        return data


def view_users(request, object_, url, template='permissions/users.html'):
    """
    Generic view for rendering a list of Users who have permissions on an
    object.
    
    This view does not perform any validation of user permissions, that should
    be done in another view which calls this view for display
    
    @param request: HttpRequest
    @param object: object to list Users and Groups for
    @param url: base url for editing permissions
    @param template: template for rendering User/Group list.
    """
    users = get_users(object_)
    groups = get_groups(object_)
    return render_to_response(template, \
            {'object': object_,
             'users':users,
             'groups':groups,
             'url':url}, \
        context_instance=RequestContext(request),
    )


def view_permissions(request, object_, url, user_id=None, group_id=None,
                key='id',
                user_template='permissions/user_row.html',
                group_template='permissions/group_row.html'
                ):
    """
    Update a User or Group permissions on an object.  This is a generic view
    intended to be used for editing permissions on any object.  It must be
    configured with a model and url.  It may also be customized by adding custom
    templates or changing the pk field.
    
    @param object: object permissions are being set on
    @param url: name of url being edited
    @param user_id: ID of User being edited
    @param group_id: ID of Group being edited
    @param user_template: template used to render user rows
    @param group_template: template used to render group rows
    """
    if request.method == 'POST':
        form = ObjectPermissionFormNewUsers(object_, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if form.update_perms():
                # return html to replace existing user row
                form_user = form.cleaned_data['user']
                group = form.cleaned_data['group']
                if form_user:
                    return render_to_response(user_template, \
                                {'object':object_, 'user':form_user, 'url':url})
                else:
                    return render_to_response(group_template, \
                                {'object':object_, 'group':group, 'url':url})
                
            else:
                # no permissions, send ajax response to remove user
                return HttpResponse('1', mimetype='application/json')
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    if user_id:
        form_user = get_object_or_404(User, id=user_id)
        data = {'permissions':get_user_perms(form_user, object_), \
                'user':user_id}
    elif group_id:
        group = get_object_or_404(Group, id=group_id)
        data = {'permissions':get_group_perms(group, object_), \
                'group':group_id}
    else:
        data = {}
    form = ObjectPermissionFormNewUsers(object_, data)
    return render_to_response('permissions/form.html', \
                {'form':form, 'object':object_, 'user_id':user_id, \
                'group_id':group_id, 'url':url}, \
               context_instance=RequestContext(request))