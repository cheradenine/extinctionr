from django.contrib import admin

from wagtail.contrib.modeladmin.options import (
    ModelAdmin,     
    ModelAdminGroup, 
    modeladmin_register 
)


from .models import Action


class ActionAdmin(ModelAdmin):
    model = Action
    menu_icon = 'date'
    list_display = ('slug', 'name', 'when',)
    prepopulated_fields = {"slug": ("name",)}
    filter_vertical = ('photos',)
    readonly_fields = ('modified', )
    add_to_settings_menu = False
    exclude_from_explorer = False

    def status(self, obj):
        return 'live'


modeladmin_register(ActionAdmin)


