from django.contrib import admin

from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register
)
from wagtail.contrib.modeladmin.views import IndexView
from contacts.models import Contact
from .models import VolunteerRequest


# provide a custom index view to work around bug
class ContactIndexView(IndexView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.export_headings['city'] = 'City'
        self.export_headings['state'] = 'State'
        self.export_headings['zipcode'] = 'Zipcode'


class ContactAdmin(ModelAdmin):
    model = Contact
    index_view_class = ContactIndexView
    menu_label = "Contacts"
    menu_icon = "user"
    add_to_settings_menu = False
    exclude_from_explorer = False
    empty_value_display = 'unknown'
    list_select_related = ('address',)
    readonly_fields = ('created_on')
    list_display = ('email', 'first_name', 'last_name', 'phone', 'city', 'created_on')
    list_filter = (('tags', admin.RelatedOnlyFieldListFilter), 'address__city')
    list_export = (
        'created_on',
        'email',
        'first_name',
        'last_name',
        'phone',
        'city',
        'state',
        'zipcode'
    )
    search_fields = (
        'email',
        'first_name',
        'last_name',
        'address__city',
        'address__postcode',
    )

    def city(self, obj):
        if not obj.address:
            return self.empty_value_display
        return obj.address.city
    city.admin_order_field = 'address__city'

    def state(self, obj):
        if not obj.address:
            return self.empty_value_display
        return obj.address.state

    def zipcode(self, obj):
        if not obj.address:
            return self.empty_value_display
        return obj.address.postcode


class VolunteerIndexView(IndexView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.export_headings['contact_email'] = 'Email'
        self.export_headings['contact_phone'] = 'Phone'
        self.export_headings['contact_city'] = 'City'


class VolunteerRequestAdmin(ModelAdmin):
    model = VolunteerRequest
    index_view_class = VolunteerIndexView
    menu_label = 'Volunteers'
    menu_icon = "user"
    add_to_settings_menu = False
    exclude_from_explorer = False
    #  TODO: readonly_fields apparently doesn't work.
    readonly_fields = (
        'created',
        'contact',
        'message',
        'tags',
        'updated',
    )
    list_display = (
        'contact',
        'contact_email',
        'contact_phone',
        'contact_city',
        'created',
        'status',
        'updated',
        'assigned',
    )
    list_filter = (
        'status',
        ('tags', admin.RelatedOnlyFieldListFilter),
        'contact__address__city',
    )
    list_export = (
        'created',
        'contact',
        'contact_email',
        'contact_phone',
        'contact_city',
        'message',
        'replied_on',
        'assigned',
    )

    search_fields = ('contact__email', 'contact__address__city',)

    def contact_email(self, obj):
        return obj.contact.email

    contact_email.short_description = 'email'

    def contact_phone(self, obj):
        return obj.contact.phone

    contact_phone.short_description = 'phone'

    def contact_city(self, obj):
        return obj.contact.address.city

    contact_city.short_description = 'city'


class CRMGroup(ModelAdminGroup):
    menu_label = 'Contacts'
    menu_icon = 'folder-open-inverse'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (ContactAdmin, VolunteerRequestAdmin)


# When using a ModelAdminGroup class to group several ModelAdmin classes together,
# you only need to register the ModelAdminGroup class with Wagtail:
modeladmin_register(CRMGroup)
