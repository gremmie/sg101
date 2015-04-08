from django.apps import AppConfig


class WikiConfig(AppConfig):
    name = 'wiki'

    def ready(self):
        import wiki.receivers
