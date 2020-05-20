from django.contrib import admin
from .models import Circle, CircleMember, MembershipRequest, CircleJob, Couch, Signup, VolunteerRequest
from extinctionr.utils import get_contact
from markdownx.admin import MarkdownxModelAdmin


@admin.register(Circle)
class CircleAdmin(MarkdownxModelAdmin):
    list_display = ('__str__', 'modified')
    readonly_fields = ('created', 'modified', )
    list_select_related = ('parent',)
    search_fields = ('name', )
    autocomplete_fields = ('parent', )
    ordering = ('parent', 'name')
    fields = ('name', 'parent', 'purpose', 'sensitive_info', 'email', 'available_roles', 'role_description', 'color', 'created', 'modified')

    def has_view_permission(self, request, obj=None):
        if obj:
            return obj.can_manage(request.user)
        else:
            return request.user.has_perm('circles.view_circle')

    def has_change_permission(self, request, obj=None):
        if obj:
            return obj.can_manage(request.user)
        else:
            return request.user.has_perm('circles.change_circle')

    def has_module_permission(self, request):
        if not request.user.is_anonymous:
            contact = get_contact(email=request.user.email)
            return contact.circlemember_set.exists()


@admin.register(MembershipRequest)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('created', 'requestor', 'circle', 'confirmed_by', 'confirm_date')
    list_select_related = ('requestor', 'circle')
    autocomplete_fields = ('requestor', 'confirmed_by', 'circle')
    readonly_fields = ('confirm_date', )


@admin.register(CircleMember)
class CircleMemberAdmin(admin.ModelAdmin):
    list_display = ('circle', 'contact', 'role', 'join_date')
    autocomplete_fields = ('circle', 'contact')
    readonly_fields = ('join_date', )
    list_filter = ('circle',)


@admin.register(CircleJob)
class CircleJobAdmin(MarkdownxModelAdmin):
    fields = ('circle', 'title', 'job', 'asap', 'filled', 'filled_on', 'creator', 'created')
    list_display = ('circle', 'created', 'filled')
    autocomplete_fields = ('circle', 'filled')
    readonly_fields = ('created', 'filled_on', 'creator')
    list_filter = ('circle',)

    def save_model(self, request, obj, form, change):
        if not obj.creator:
            obj.creator = get_contact(email=request.user.email)
        super().save_model(request, obj, form, change)


@admin.register(Couch)
class CouchAdmin(MarkdownxModelAdmin):
    autocomplete_fields = ('owner',)
    list_display = ('owner', 'created', 'modified', 'public')
    readonly_fields = ('created', 'modified')
    list_select_related = ('owner',)
    list_filter = ('owner__address__city',)

    def has_view_permission(self, request, obj=None):
        has_perm = request.user.has_perm('circle.view_couch')
        if obj:
            return obj.is_me(request.user) or has_perm
        return has_perm

    def has_change_permission(self, request, obj=None):
        has_perm = request.user.has_perm('circles.change_couch')
        if obj:
            return obj.is_me(request.user) or has_perm
        return has_perm


@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'contact') + Signup.json_fields + ('raw_data', )
    list_display = ('contact', 'created', ) + Signup.json_fields


@admin.register(VolunteerRequest)
class VolunteerRequestAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'contact', 'message')
    list_display = ('contact', 'contact_email', 'contact_city', 'created')
    list_filter = ('tags', 'contact__address__city')

    def contact_email(self, obj):
        return obj.contact.email

    contact_email.short_description = 'email'

    def contact_city(self, obj):
        return obj.contact.address.city
    
    contact_city.short_description = 'city'
