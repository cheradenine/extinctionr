from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomImage
from .utils import clear_image_exif


@receiver(post_save, sender=CustomImage)
def post_process_image(sender, instance, created, **kwargs):
    if created:
        clear_image_exif(instance.file)
