from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.users.forms import UserEditForm


class CustomUserEditForm(UserEditForm):
    username = forms.CharField(required=True, label=_("Username"))


class CustomUserCreationForm(UserEditForm):
    username = forms.CharField(required=True, label=_("Username"))
