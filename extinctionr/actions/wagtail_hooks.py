from django.contrib.admin.utils import quote

from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.mixins import ThumbnailMixin
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register
)
from wagtail.contrib.modeladmin.views import EditView, CreateView

from .models import Action


class ActionButtonHelper(ButtonHelper):
    view_button_classnames = [
        'button-small', 'button-secondary', 'icon', 'icon-site'
    ]

    def view_button(self, obj):
        text = 'View'
        return {
            'url': obj.get_absolute_url(),  # decide where the button links to
            'label': text,
            'classname': self.finalise_classname(self.view_button_classnames),
            'title': '{0} this {1}'.format(text, self.verbose_name)
        }

    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None, classnames_exclude=None):
        btns = super().get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)
        if 'view' not in (exclude or []):
            # Find the edit button.
            for i, btn in enumerate(btns):
                if btn['label'] == 'Edit':
                    break
            # Insert after edit button.
            btns.insert(i + 1, self.view_button(obj))
        return btns


# Mixin that enables save and continue editing.
class SaveAndContinue:
    def get_edit_url(self):
        return self.url_helper.get_action_url('edit', quote(self._instance.pk))

    def form_valid(self, form):
        # Have to save instance this form is working with:
        self._instance = form.instance
        return super().form_valid(form)

    def get_success_message_buttons(self, instance):
        if self._is_continue():
            return None
        return super().get_success_message_buttons(instance)

    def get_success_url(self):
        # Enables 'save and continue' mode of editing.
        if self._is_continue():
            return self.get_edit_url()
        return super().get_success_url()

    def _is_continue(self):
        return self.request.POST.get('_continue') == 'Save and continue editing'


class ActionEditView(SaveAndContinue, EditView):
    def view_url(self):
        get_absolute_url = getattr(self.instance, 'get_absolute_url', None)
        if callable(get_absolute_url):
            return get_absolute_url()


class ActionCreateView(SaveAndContinue, CreateView):
    def view_url(self):
        return None


class ActionAdmin(ThumbnailMixin, ModelAdmin):
    model = Action
    button_helper_class = ActionButtonHelper
    edit_view_class = ActionEditView
    create_view_class = ActionCreateView
    menu_icon = 'date'
    list_display = ('name', 'slug', 'admin_thumb', 'when',)
    filter_vertical = ('photos',)
    readonly_fields = ('modified',)
    add_to_settings_menu = False
    exclude_from_explorer = False
    thumb_image_field_name = 'image'
    thumb_image_filter_spec = 'fill-112x63'
    thumb_image_width = 112

    def create_view(self, request):
        view = super().create_view(request)
        self._enable_slug_editing(view)
        return view

    def _enable_slug_editing(self, view):
        ''' Tricks the editor into enabling some javascript normally
            used on Page models to sync the title with the slug
        '''
        context_data = getattr(view, 'context_data', None)
        if context_data:
            form = context_data['form']
            form.fields['name'].widget.attrs['id'] = 'id_title'
            form.fields['slug'].widget.attrs['id'] = 'id_slug'


modeladmin_register(ActionAdmin)
