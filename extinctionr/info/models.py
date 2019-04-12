from django.db import models
from django.urls import reverse
from markdownx.models import MarkdownxField
from django.utils.timezone import now


class PressReleaseManager(models.Manager):
    def released(self):
        return self.get_queryset().filter(released__lt=now()).order_by('released')


class PressRelease(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True)
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    released = models.DateTimeField(db_index=True, null=True, blank=True, help_text='Release dates in the future will not be visible on the site')
    body = MarkdownxField(default='', blank=True)

    objects = PressReleaseManager()

    @property
    def is_released(self):
        return self.released and self.released <= now()

    def get_absolute_url(self):
        return reverse('extinctionr.info:pr-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title
