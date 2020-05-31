# Generated by Django 3.0.6 on 2020-05-31 21:02

from django.db import migrations
import extinctionr.vaquita.blocks
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.embeds.blocks
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0008_remove_storypage_anonymous'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storypage',
            name='content',
            field=wagtail.core.fields.StreamField([('paragraph', wagtail.core.blocks.RichTextBlock(features=['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul'])), ('markdown', extinctionr.vaquita.blocks.ZOrderMarkdownBlock(icon='code')), ('image', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock()), ('caption', wagtail.core.blocks.CharBlock(required=False))])), ('carousel', extinctionr.vaquita.blocks.ImageCarouselBlock()), ('quote', wagtail.core.blocks.BlockQuoteBlock()), ('embedded_content', wagtail.core.blocks.StructBlock([('embed', wagtail.embeds.blocks.EmbedBlock(label='url', required=True)), ('caption', wagtail.core.blocks.CharBlock(help_text='Enter a caption', label='caption')), ('use_as_hero', wagtail.core.blocks.BooleanBlock(help_text='Use as hero image', label='hero', required=False))]))]),
        ),
    ]
