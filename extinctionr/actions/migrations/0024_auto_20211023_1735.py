# Generated by Django 3.0.13 on 2021-10-23 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0023_auto_20200531_1702'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='contact_email',
            field=models.TextField(default='', help_text='Contact info of event organizer.', null=True),
        ),
        migrations.AlterField(
            model_name='action',
            name='location',
            field=models.TextField(blank=True, default='', help_text='Event location will be converted to a google maps link, unless you format it as a Markdown link -- [link text](http://example.com)'),
        ),
    ]