from django.apps import AppConfig


class DownloadsConfig(AppConfig):
    name = 'downloads'

    def ready(self):
        import downloads.receivers
