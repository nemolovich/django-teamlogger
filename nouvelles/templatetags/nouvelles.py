from django import template
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import resolve
from django.db.models import QuerySet

from nouvelles import settings, __version__
from nouvelles.models import Article

register = template.Library()


@register.inclusion_tag('templatetags/header.html', takes_context=True)
def nouvelles_header(context):
    """Build a navigation bar"""
    request = context['request']
    path_name = resolve(request.path_info).url_name
    redirect_path = request.path

    if path_name == 'login':
        redirect_path = None

    return {
        'path_name': path_name,
        'redirect_path': redirect_path,
        'user': request.user,
        'perms': context.get('perms', None),
        'site_name': settings.SITE_NAME,
        'search_query': request.GET.get('q', '')
    }


@register.inclusion_tag('templatetags/footer.html')
def nouvelles_footer():
    """Build the footer"""
    return {
        'site_name': settings.SITE_NAME,
        'app_version': __version__,
    }


@register.inclusion_tag('templatetags/site_title.html')
def site_title(page_title):
    """Build a browser title for the page"""
    return {'page_title': page_title, 'site_name': settings.SITE_NAME}


@register.inclusion_tag('templatetags/format_articles_list.html')
def format_articles_list(articles: QuerySet, show_dates: bool = False):
    ordered_articles = []

    if show_dates:
        paginated_articles = Article.objects.filter(id__in=articles.values_list('id', flat=True)) \
            .filter(effective_date__in=articles.values_list('effective_date', flat=True)) \
            .select_related('author') \
            .prefetch_related('tags')
        for date in paginated_articles.dates('effective_date', 'day', order='DESC'):
            ordered_articles.append(date)
            ordered_articles.extend(paginated_articles.filter(effective_date=date).order_by('-creation_date'))
    else:
        ordered_articles = articles.select_related('author').prefetch_related('tags')

    return {'articles': ordered_articles}


@register.inclusion_tag('templatetags/article.html', takes_context=True)
def article(context, article):
    request = context['request']
    return {'article': article,
            'perms': context.get('perms', None),
            'user': request.user, }


@register.simple_tag(takes_context=True)
def paginated_url(context, view_name, page, page_arg_name='page'):
    from django.urls import reverse
    req_params = context.request.GET.copy()

    if req_params.get(page_arg_name):
        req_params.pop(page_arg_name)
        req_params.update({page_arg_name: page})
    else:
        req_params.update({page_arg_name: page})

    return "%s?%s" % (reverse(view_name), req_params.urlencode())


@register.filter
def class_name(obj):
    return obj.__class__.__name__


@register.filter
def user_full_name(user):
    if not isinstance(user, AbstractUser):
        return

    return user.get_full_name() if user.get_full_name() else user.username


@register.filter
def user_initials(user):
    if not isinstance(user, AbstractUser):
        return

    return "".join(item[0].upper() for item in user_full_name(user).split(' ', 1))
