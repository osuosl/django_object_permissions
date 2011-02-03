import json

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.safestring import SafeString

from object_permissions import get_user_perms, get_group_perms, \
    get_model_perms, grant, revoke, get_users, get_groups
from object_permissions.models import Group
from object_permissions.signals import view_add_user, view_remove_user, \
    view_edit_user


class ObjectPermissionForm(forms.Form):
    """
    Form used for editing permissions
    """
    permissions = forms.MultipleChoiceField(required=False, \
                                            widget=forms.CheckboxSelectMultiple)
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    group = forms.ModelChoiceField(queryset=Group.objects.all(), \
                                   required=False)
    
    choices = {}
    """ dictionary used for caching the choices for specific models """
    
    def __init__(self, obj, *args, **kwargs):
        """
        @param object - the object being granted permissions
        """
        super(ObjectPermissionForm, self).__init__(*args, **kwargs)
        self.object = obj
        
        self.fields['permissions'].choices = self.get_choices(obj)

    @classmethod
    def get_choices(cls, obj):
        """ helper method for getting choices for a model.  This method uses an
        internal cache to store the choices. """
        try: 
            return ObjectPermissionForm.choices[obj.__class__]
        except KeyError:
            # choices weren't built yet.
            choices = []
            model_perms = get_model_perms(obj.__class__)
            
            for perm, params in model_perms.items():
                display = params.copy()
                if 'label' not in display:
                    display['label'] = perm
                choices.append((perm, display))
            ObjectPermissionForm.choices[obj.__class__] = choices
            return choices

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
            
            old_perms = grantee.get_perms(self.object)
            if old_perms:
                # not new, has perms already
                data['new'] = False
                
            elif not perms:
                # new, doesn't have perms specified
                msg = """You must grant at least 1 permission for new users and groups"""
                self._errors["permissions"] = self.error_class([msg])
                
            else:
                # new, perms specified
                data['new'] = True
        
        return data


def view_users(request, object_, url, \
               template='object_permissions/permissions/users.html'):
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
    users = get_users(object_, groups=False)
    groups = get_groups(object_)
    return render_to_response(template, \
            {'object': object_,
             'users':users,
             'groups':groups,
             'url':url}, \
        context_instance=RequestContext(request),
    )


def view_permissions(request, obj, url, user_id=None, group_id=None,
                key='id',
                user_template='object_permissions/permissions/user_row.html',
                group_template='object_permissions/permissions/group_row.html'
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
        form = ObjectPermissionFormNewUsers(obj, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            form_user = form.cleaned_data['user']
            group = form.cleaned_data['group']
            edited_user = form_user if form_user else group
            
            if form.update_perms():
                # send correct signal based on new or edited user
                if data['new']:
                    view_add_user.send(sender=obj.__class__, \
                                       editor=request.user, \
                                       user=edited_user, obj=obj)
                else:
                    view_edit_user.send(sender=obj.__class__, \
                                        editor=request.user, \
                                        user=edited_user, obj=obj)
                
                # return html to replace existing user row
                if form_user:
                    return render_to_response(user_template, \
                                {'object':obj, 'user':form_user, 'url':url})
                else:
                    return render_to_response(group_template, \
                                {'object':obj, 'group':group, 'url':url})
                
            else:
                # no permissions, send ajax response to remove user
                view_remove_user.send(sender=obj.__class__, \
                                      editor=request.user, user=edited_user, \
                                      obj=obj)
                return HttpResponse('1', mimetype='application/json')
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    if user_id:
        form_user = get_object_or_404(User, id=user_id)
        data = {'permissions':get_user_perms(form_user, obj), \
                'user':user_id}
    elif group_id:
        group = get_object_or_404(Group, id=group_id)
        data = {'permissions':get_group_perms(group, obj), \
                'group':group_id}
    else:
        data = {}
        
    form = ObjectPermissionFormNewUsers(obj, data)
    
    return render_to_response('object_permissions/permissions/form.html', \
                {'form':form, 'object':obj, 'user_id':user_id, \
                'group_id':group_id, 'url':url}, \
               context_instance=RequestContext(request))


@login_required
def all_permissions(request, id, \
                    template="object_permissions/permissions/objects.html"):
    """
    Generic view for displaying permissions on all objects.
    
    @param id: id of user
    @param template: template to render the results with, default is
    permissions/objects.html
    """
    user = request.user
    
    if not (user.is_superuser or id==user.pk):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if user.is_superuser:
        user = get_object_or_404(User, pk=id)
    
    perm_dict = user.get_all_objects_any_perms(groups=False)
    
    try:
        del perm_dict[Group]
    except KeyError:
        pass
    
    return render_to_response(template, \
            {'persona':user, 'perm_dict':perm_dict}, \
        context_instance=RequestContext(request),
    )