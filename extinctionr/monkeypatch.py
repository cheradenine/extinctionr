"""
For monkeypatching things in third party libraries
"""
from django.urls import reverse
from django.contrib import admin


def get_absolute_url(self):
    return reverse('common:view_user', kwargs={'pk': self.id})


def do_monkeypatch():
    from contacts.models import Contact
    from common.models import User
    from taggit.managers import TaggableManager
    from wiki.plugins.images.wiki_plugin import ImagePlugin

    # give users an absolute url
    User.get_absolute_url = get_absolute_url

    def _contact_str(obj):
        return '{} {}'.format(obj.first_name, obj.last_name)

    Contact.__str__ = _contact_str
    TaggableManager(blank=True).contribute_to_class(Contact, 'tags')

    admin.site.unregister(Contact)
    # overriding the default admin to add some features
    @admin.register(Contact)
    class ContactAdmin(admin.ModelAdmin):
        search_fields = ('first_name', 'last_name', 'email', 'postcode')
        list_display = ('email', 'first_name', 'last_name', 'phone', 'created_on')
        list_filter = ('tags', 'address__city')
        list_select_related = ('address', )

    # fix the icon on the image macro
    ImagePlugin.sidebar['icon_class'] = 'fa-images'
