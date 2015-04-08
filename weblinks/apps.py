from django.apps import AppConfig


class WeblinksConfig(AppConfig):
    name = 'weblinks'
    verbose_name = 'Web Links'

    def ready(self):
        import weblinks.receivers
