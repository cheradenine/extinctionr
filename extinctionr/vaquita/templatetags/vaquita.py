import urllib

from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def social_url(context, url, service, message=''):
    request = context['request']
    pageurl = request.build_absolute_uri(url)
    if service == 'fb':
        return 'https://www.facebook.com/sharer/sharer.php?u={0}'.format(pageurl)
    if service == 'twitter':
        title = urllib.parse.quote(message)
        url = 'https://twitter.com/share?url={0}&text={1}&hashtags={2}'.format(
            pageurl, title, 'ExtinctionRebellion,XRBoston'
        )
        return url
    if service == 'email':
        url = 'mailto:?subject=' + message
        url += '&body=' + message + '%0D%0A' + pageurl
        return url
