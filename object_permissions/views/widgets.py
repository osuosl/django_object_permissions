from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.utils import simplejson


def search_users(request):
    """ search users and groups and return results as json """
    if 'query' not in request.GET:
        return HttpResponse()

    term = request.GET['query']
    limit = 10
    data = simplejson.dumps(search_users_and_groups(term, limit))
    return HttpResponse(data, mimetype="application/json")


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
    f = 'user:%s:%s'
    users = [f % (i['pk'], i['username']) for i in users]
    f = 'group:%s:%s'
    groups = [f % (i['pk'], i['name']) for i in groups]

    # merge and trim list if needed
    merged = users + groups
    # TODO: need to sort by names
    #merged = sorted(merged, key=lambda x: x['label'])
    merged = merged if len(merged) < limit else merged[:limit]

    return {
        'query':term,
        'suggestions':merged
    }