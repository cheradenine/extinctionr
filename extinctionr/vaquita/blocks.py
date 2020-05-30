from django import forms

from wagtail.core.blocks import (
    CharBlock, StructBlock, ListBlock
)
from wagtail.images.blocks import ImageChooserBlock
from wagtailmarkdown.blocks import MarkdownBlock


class ImageCarouselBlock(ListBlock):
    def __init__(self):
        super().__init__(StructBlock([
            ('image', ImageChooserBlock()),
            ('caption', CharBlock(max_length=255, required=False)),
        ]))

    class Meta:
        icon = 'image'
        template = 'blocks/image_carousel_block.html'


class ZOrderMarkdownBlock(MarkdownBlock):
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
