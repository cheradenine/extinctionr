import urllib
from django import template
from django.utils.timezone import now

from extinctionr.news.models import FeaturedStory
from extinctionr.actions.models import Action

register = template.Library()

@register.filter('elide_pages')
def elide_pages(range, cur_page):
    pages = []
    skip = False
    for p in range:
        if p <= 2 or p >= range.stop - 2:
            pages.append(p)
            skip = False
        elif cur_page-3 <= p <= cur_page+3:
            pages.append(p)
            skip = False
        elif not skip:        
            pages.append(-1)
            skip = True
    return pages


@register.inclusion_tag("news/story_sidebar.html")
def story_sidebar(*args, **kwargs):
    featured = FeaturedStory.objects.all().order_by('-story__first_published_at')
    return {'featured_stories': featured}

@register.inclusion_tag("news/story_mini_card.html")
def mini_card(story):
    return {'story' : story.specific}

@register.inclusion_tag('news/upcoming_actions.html')
def upcoming_actions(*args, **kwargs):
    try:
        actions = Action.objects.filter(public=True, when__gte=now()).order_by('when')[0:3]
    except IndexError:
        actions = None
    return {'actions': actions}
