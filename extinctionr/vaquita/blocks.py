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
        media = super().media
        return media + forms.Media(
            css={'all': ('css/xr-codemirror.css',)}
        )
