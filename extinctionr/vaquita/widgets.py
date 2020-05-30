from django import forms
from wagtailmarkdown.widgets import MarkdownTextarea


class ZOrderMarkdownTextarea(MarkdownTextarea):
    @property
    def media(self):
        return forms.Media(
            css={
                'all': (
                    'wagtailmarkdown/css/simplemde.min.css',
                    'css/xr-codemirror.css',
                )
            },
            js=(
                'wagtailmarkdown/js/simplemde.min.js',
                'wagtailmarkdown/js/simplemde.attach.js',
            )
        )
