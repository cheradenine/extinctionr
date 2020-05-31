from datetime import date
from pathlib import PurePath

from django.db import models

from wagtail.images.models import Image, AbstractImage, AbstractRendition


def _filepath_with_date(filepath):
    path = PurePath(filepath)
    today = date.today()
    return path.parent / str(today.year) / str(today.month) / str(today.day) / path.name


class CustomImage(AbstractImage):
    admin_form_fields = Image.admin_form_fields

    def get_upload_to(self, filename):
        fullpath = super().get_upload_to(filename)
        return _filepath_with_date(fullpath)


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )

    def get_upload_to(self, filename):
        fullpath = super().get_upload_to(filename)
        return _filepath_with_date(fullpath)
