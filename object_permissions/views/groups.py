import json

from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, \
    HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from object_permissions import get_model_perms, grant, revoke, get_user_perms
from object_permissions.signals import view_add_user, view_remove_user, \
    view_edit_user, view_group_edited, view_group_created, view_group_deleted
from object_permissions.views.permissions import ObjectPermissionForm


class GroupForm(forms.ModelForm):
    """
    Form for editing Groups
    """
    class Meta:
        model = Group


class UserForm(forms.Form):
    """
    Base form for dealing with users
    """
    group = None
    user = forms.ModelChoiceField(queryset=User.objects.all())
    
    def __init__(self, group=None, *args, **kwargs):
        self.group=group
        super(UserForm, self).__init__(*args, **kwargs)


class AddUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is not in group already """
        user = self.cleaned_data['user']
        if self.group.user_set.filter(id=user.id).exists():
            raise forms.ValidationError("User is already a member of this group")
        return user


class RemoveUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is in group """
        user = self.cleaned_data['user']
        if not self.group.user_set.filter(id=user.id).exists():
            raise forms.ValidationError("User is not a member of this group")
        return user


@login_required
def list(request):
    """
    List all user groups.
    """
    user = request.user
    if request.user.is_superuser:
        groups = Group.objects.all()
    else:
        groups = user.get_objects_any_perms(Group, ['admin'])
        if not groups:
            return HttpResponseForbidden()

    return render_to_response("object_permissions/group/list.html", \
                              {'groups':groups}, \
                              context_instance=RequestContext(request)) 


@login_required
def detail(request, id=None, template='object_permissions/group/detail.html'):
    """
    Display group details
    
    @param id: id of Group
    """
    group = get_object_or_404(Group, id=id) if id else None
    user = request.user
    
    if not (user.is_superuser or user.has_perm('admin', group)):
        return HttpResponseForbidden()
    
    method = request.method
    if method == 'GET':
        return render_to_response(template,
                            {'object':group,
                             'group':group,
                             'users':group.user_set.all(),
                             'url':reverse('usergroup-permissions', args=[id])
                             }, \
                              context_instance=RequestContext(request))
    
    elif method == 'POST':
        if request.POST:
            # form data, this was a submission
            form = GroupForm(request.POST, instance=group)
            if form.is_valid():
                new = False if group else True
                group = form.save()
                if new:
                    view_group_created.send(sender=group, editor=user)
                else:
                    view_group_edited.send(sender=group, editor=user)
                    
                return render_to_response( \
                    "object_permissions/group/group_row.html", \
                    {'group':group}, \
                    context_instance=RequestContext(request))
            
            content = json.dumps(form.errors)
            return HttpResponse(content, mimetype='application/json')
        
        else:
            form = GroupForm(instance=group)
        
        return render_to_response("object_permissions/group/edit.html", \
                        {'group':group, 'form':form}, \
                        context_instance=RequestContext(request))
    
    elif method == 'DELETE':
        group.delete()
        view_group_deleted.send(sender=group, editor=user)
        return HttpResponse('1', mimetype='application/json')

    return HttpResponseNotAllowed(['PUT', 'HEADER'])


@login_required
def add_user(request, id):
    """
    ajax call to add a user to a Group
    
    @param id: id of Group
    """
    editor = request.user
    group = get_object_or_404(Group, id=id)
    
    if not (editor.is_superuser or editor.has_perm('admin', group)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = AddUserForm(group, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            group.user_set.add(user)
            
            # signal
            view_add_user.send(sender=editor, user=user, obj=group)
            
            # return html for new user row
            url = reverse('usergroup-permissions', args=[id])
            return render_to_response( \
                        "object_permissions/permissions/user_row.html", \
                        {'user':user, 'object':group, 'url':url})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    form = AddUserForm()
    return render_to_response("object_permissions/group/add_user.html",\
                              {'form':form, 'group':group}, \
                              context_instance=RequestContext(request))


@login_required
def remove_user(request, id):
    """
    Ajax call to remove a user from an Group
    
    @param id: id of Group
    """
    editor = request.user
    group = get_object_or_404(Group, id=id)
    
    if not (editor.is_superuser or editor.has_perm('admin', group)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET')

    form = RemoveUserForm(group, request.POST)
    if form.is_valid():
        user = form.cleaned_data['user']
        group.user_set.remove(user)
        user.revoke_all(group)
        
        # signal
        view_remove_user.send(sender=editor, user=user, obj=group)
        
        # return success
        return HttpResponse('1', mimetype='application/json')
        
    # error in form return ajax response
    content = json.dumps(form.errors)
    return HttpResponse(content, mimetype='application/json')


@login_required
def user_permissions(request, id, user_id=None):
    """
    Ajax call to update a user's permissions
    
    @param id: id of Group
    """
    editor = request.user
    group = get_object_or_404(Group, id=id)
    
    if not (editor.is_superuser or editor.has_perm('admin', group)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = ObjectPermissionForm(group, request.POST)
        if form.is_valid():
            form.update_perms()
            user = form.cleaned_data['user']
            
            # send signal
            view_edit_user.send(sender=editor, user=user, obj=group)
            
            # return html to replace existing user row
            url = reverse('usergroup-permissions', args=[id])
            return render_to_response( \
                "object_permissions/permissions/user_row.html", \
                {'object':group, 'user':user, 'url':url})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')
    
    # render a form for an existing user only
    form_user = get_object_or_404(User, id=user_id)
    data = {'permissions':get_user_perms(form_user, group), 'user':user_id}
    form = ObjectPermissionForm(group, data)
    return render_to_response("object_permissions/permissions/form.html", \
                    {
                    'form':form,
                     'user_id':user_id,
                     'url':reverse('usergroup-permissions', args=[group.id])
                     }, \
                    context_instance=RequestContext(request))
    

@login_required
def all_permissions(request, id, \
                    template='object_permissions/permissions/objects.html' ):
    """
    Generic view for displaying permissions on all objects.
    
    @param id: id of group
    @param template: template to render the results with, default is
    permissions/objects.html
    """
    user = request.user
    group = get_object_or_404(Group, pk=id)
    
    if not (user.is_superuser or group.user_set.filter(pk=user.pk).exists()):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    perm_dict = group.get_all_objects_any_perms()
    
    try:
        del perm_dict[Group]
    except KeyError:
        pass
    
    return render_to_response(template, \
            {'persona':group, 'perm_dict':perm_dict}, \
        context_instance=RequestContext(request),
    )
