from django.apps import AppConfig


class VaquitaAppConfig(AppConfig):
    name = 'extinctionr.vaquita'
    label = 'vaquita'

    def ready(self):
        from . import signals  # noqa F401
