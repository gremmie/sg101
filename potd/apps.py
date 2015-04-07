from django.apps import AppConfig


class PotdConfig(AppConfig):
    name = 'potd'
    verbose_name = 'Photo of the Day'
    label = 'potd'

    def ready(self):
        import potd.receivers
