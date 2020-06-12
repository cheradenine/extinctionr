from io import BytesIO
from pathlib import Path
import requests
from urllib.parse import urlparse

from django.core.files.images import ImageFile
from wagtail.core.models import Collection

from .models import CustomImage


def test_image_import():
    importer = ImageImporter('Media Images')
    importer.import_from_file('/Users/johnburk/projects/xr/extinctionr/fake_ad.jpg')


class ImageImporter:
    def __init__(self, collection_name=''):
        if collection_name:
            self.collection = Collection.objects.filter(name=collection_name).get()
        else:
            self.collection = None

    def import_from_url(self, url):
        response = requests.get(url)
        path = Path(urlparse(url).path)
        byte_stream = BytesIO(response.content)
        self._import(path.name, byte_stream)

    def import_from_file(self, filename, title=None):
        with open(filename, "rb") as byte_stream:
            self._import(title if title else filename, byte_stream)

    def _import(self, name, byte_stream):
        image = CustomImage(
            title=name,
            file=ImageFile(byte_stream, name=name)
        )
        image.collection = self.collection
        image.save()
