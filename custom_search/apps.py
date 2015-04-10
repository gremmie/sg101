from django.apps import AppConfig


class CustomSearchConfig(AppConfig):
    name = 'custom_search'
    verbose_name = 'Custom Search'

    def ready(self):
        import custom_search.receivers
