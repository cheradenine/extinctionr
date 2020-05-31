from django import forms
from wagtailmarkdown.widgets import MarkdownTextarea


class ZOrderMarkdownTextarea(MarkdownTextarea):
    @property
    def media(self):
        media = super().media
        return media + forms.Media(
            css={'all': ('css/xr-codemirror.css',)}
        )
