from pathlib import Path
import logging

from django.core.files.images import ImageFile
from wagtail.core.models import Collection

from PIL import Image

from .models import CustomImage

logger = logging.getLogger('vaquita.utils')


class ImageImporter:
    def __init__(self, collection_name=''):
        if collection_name:
            try:
                col = Collection.objects.get(name=collection_name)
            except Collection.DoesNotExist:
                root_col = Collection.get_first_root_node()
                col = root_col.add_child(name=collection_name)
            self.collection = col
        else:
            self.collection = None
        self.images = {}

    def import_from_photo(self, photo):
        if photo.photo.path in self.images:
            return self.images[photo.photo.path]
        image = self.import_from_file(
            photo.photo.path,
            photo.caption,
            uploaded_by_user=photo.uploader,
            created_at=photo.created
        )
        self.images[photo.photo.path] = image
        return image

    def import_from_file(self, filename, title=None, **kwargs):
        p = Path(filename)
        with p.open("rb") as byte_stream:
            return self._import(p.name, byte_stream, title, **kwargs)

    def _import(self, name, byte_stream, title=None, **kwargs):
        image = CustomImage.objects.create(
            file=ImageFile(byte_stream, name=name),
            title=title if title else name,
            **kwargs
        )
        image.collection = self.collection
        image.save()
        return image


def clear_image_exif(file_obj):
    img = Image.open(file_obj.path)
    try:
        img_no_exif = Image.new(img.mode, img.size)
        img_no_exif.putdata(list(img.getdata()))
        img_no_exif.save(file_obj.path)
    except OSError as err:
        logger.error(
            'failed to clear exif metadata from {0}: {1}'.format(file_obj.path, err)
        )
