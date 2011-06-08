from sys import stdout
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from object_log.models import LogItem, LogAction

class Command(BaseCommand):
    args = '[LOG_KEY LOG_KEY ...]'
    help = 'Rebuilds object log cache for the given log types.'

    def handle(self, *args, **options):
        rebuild_cache(*args)


def rebuild_cache(*args):
    """
    rebuild cache for list of apps passed in.  if no apps specified then
    all apps will be rebuilt
    """
    if not len(args):
        args = LogAction.objects.all().values_list('name', flat=True)
    map(_rebuild_cache, args)
    stdout.write('\n')
    stdout.flush()


def _rebuild_cache(key):
    """
    Rebuild the log cache for all entries of the given type.  If the type has no
    cache builder then it is ignored    
    """
    action = LogAction.objects.get_from_cache(key)
    if action.build_cache is None:
        return

    write = stdout.write
    flush = stdout.flush

    for entry in action.entries.all().select_related('user').iterator():
        entry.data = action.build_cache(entry.user,
                                        entry.object1,
                                        entry.object2,
                                        entry.object3,
                                        entry.data)
        entry.save(force_update=True)
        write('.')
        flush()