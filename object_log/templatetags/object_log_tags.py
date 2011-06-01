from django.template import Library
from django.utils.safestring import SafeString

register = Library()

@register.filter()
def render_context(log_item, context):
    """
    helper tag needed for adding extra context when rendering a LogItem
    """
    return SafeString(log_item.render(**context))


@register.simple_tag
def permalink(obj, display=None):
    """
    Return a link for an object if it as a get_absolute_url method.  Not all
    models will have this.  Models that do not have the method will be rendered
    as text
    """
    display = display if display else obj
    if hasattr(obj, 'get_absolute_url'):
        return '<a href="%s">%s</a>' % (obj.get_absolute_url(), display)
    else:
        return obj