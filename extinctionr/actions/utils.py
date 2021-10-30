from markdown import markdown
from html.parser import HTMLParser
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _



# Need to pull the href attribute out of the link.
class HrefExtractor(HTMLParser):
    def __init__(self, link_tag):
        super().__init__()
        self.href = None
        self.feed(link_tag)

    def handle_starttag(self, tag, attrs):
        if tag == "a" and self.href is None:
            hrefs = [val for name, val in attrs if name == "href"]
            self.href = hrefs[0]


def extract_href(link_tag):
    return HrefExtractor(link_tag).href


def markdown_link_validator(md):
    html = markdown(md)
    href = extract_href(html)
    if href is None:
        raise ValidationError(_('Invalid mardkdown link: %(value)s'), params={'value': md})
    return href