from datetime import date
from pathlib import PurePath

from django.db import models

from wagtail.images.models import Image, AbstractImage, AbstractRendition


def _filepath_with_date(filepath, created_at):
    path = PurePath(filepath)
    return path.parent / str(created_at.year) / str(created_at.month) / path.name


class CustomImage(AbstractImage):
    admin_form_fields = Image.admin_form_fields

    def get_upload_to(self, filename):
        fullpath = super().get_upload_to(filename)
        created_at = self.created_at if self.created_at else date.today()
        return _filepath_with_date(fullpath, created_at)


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )

    def get_upload_to(self, filename):
        return self.image.get_upload_to(filename)
