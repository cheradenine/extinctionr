from io import BytesIO
from pathlib import Path
import requests
from urllib.parse import urlparse

from django.core.files.images import ImageFile
from wagtail.core.models import Collection

from PIL import Image

from .models import CustomImage


class ImageImporter:
    def __init__(self, collection_name=''):
        if collection_name:
            self.collection, _ = Collection.objects.get_or_create(
                name=collection_name
            )
        else:
            self.collection = None

    def import_from_url(self, url):
        response = requests.get(url)
        path = Path(urlparse(url).path)
        byte_stream = BytesIO(response.content)
        return self._import(path.name, byte_stream)

    def import_from_photo(self, photo):
        # see if this file already exists:
        path = Path(photo.photo.path)
        images = CustomImage.filter(file__path__endswith=path.name)
        if images.count() > 0:
            return images.first()
        return self.import_from_file(
            photo.photo.path,
            photo.caption,
            uploaded_by_user=photo.uploader,
            created_at=photo.created
        )

    def import_from_file(self, filename, title=None, **kwargs):
        p = Path(filename)
        if not title:
            title = p.name
        with p.open("rb") as byte_stream:
            return self._import(title, byte_stream, **kwargs)

    def _import(self, name, byte_stream, **kwargs):
        image = CustomImage.objects.create(
            file=ImageFile(byte_stream, name=name),
            title=name,
            **kwargs
        )
        image.collection = self.collection
        image.save()
        return image


def clear_image_exif(file_obj):
    img = Image.open(file_obj.path)
    img_no_exif = Image.new(img.mode, img.size)
    img_no_exif.putdata(list(img.getdata()))
    img_no_exif.save(file_obj.path)
