from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.utils import simplejson


def search_users(request):
    """ search users and groups and return results as json """
    if 'query' not in request.GET:
        return HttpResponse()

    term = request.GET['query']
    limit = 10
    if request.GET.get("groups", 'True') == 'True':
        data = simplejson.dumps(search_users_and_groups(term, limit))
    else:
        data = simplejson.dumps(search_users_only(term, limit))
    return HttpResponse(data, mimetype="application/json")

def search_users_only(term=None, limit=10):
    """
    Returns a list of the top N matches from Users with a name
    starting with term
 
    @param term: the term to search for
    @param limit: the number of results to return
    """
     
    if term:
        users = User.objects.filter(username__istartswith=term)
    else:
        users = User.objects.all()
     
    users = users.values('pk', 'username')
     
    if limit: 
        users = users[:limit]
     
    # format list better for the interface
    f = 'user'
    users = [(i['username'], (f,i['pk'])) for i in users]
     
    # sort, trim, and unzip list into suggestions/data (if needed)
    users = sorted(users, key=lambda x: x[0]) 
    users = users if len(users) < limit else users[:limit]
    suggestions, data = zip(*users) if users else ((),())
 
    return {
        'query':term,
        'suggestions':suggestions,
        'data':data
    }

def search_users_and_groups(term=None, limit=10):
    """
    Returns a list of the top N matches from Groups and Users with a name
    starting with term

    @param term: the term to search for
    @param limit: the number of results to return
    """
    
    if term:
        users = User.objects.filter(username__istartswith=term)
        groups = Group.objects.filter(name__istartswith=term)
    else:
        users = User.objects.all()
        groups = Group.objects.all()

    users = users.values('pk', 'username')
    groups = groups.values('pk', 'name')

    if limit:
        users = users[:limit]
        groups = groups [:limit]

    # format lists better for the interface
    f = 'user'
    users = [(i['username'], (f,i['pk'])) for i in users]
    f = 'group'
    groups = [(i['name'], (f,i['pk'])) for i in groups]

    # merge, sort, trim, and unzip list into suggestions/data (if needed)
    merged = users + groups
    merged = sorted(merged, key=lambda x: x[0])
    merged = merged if len(merged) < limit else merged[:limit]
    suggestions, data = zip(*merged) if merged else ((),())

    return {
        'query':term,
        'suggestions':suggestions,
        'data':data
    }
