from django.apps import AppConfig


class BioConfig(AppConfig):
    name = 'bio'
    verbose_name = 'Biography'

    def ready(self):
        import bio.receivers
