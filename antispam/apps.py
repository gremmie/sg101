from django.apps import AppConfig


class AntiSpamConfig(AppConfig):
    name = 'antispam'
    verbose_name = 'Anti-Spam'

    def ready(self):
        import antispam.receivers
