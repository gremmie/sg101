from django.apps import AppConfig
import django.contrib.auth.views

from antispam.decorators import log_auth_failures


class AntiSpamConfig(AppConfig):
    name = 'antispam'
    verbose_name = 'Anti-Spam'

    def ready(self):
        import antispam.receivers

        # Install rate limiting on auth login
        django.contrib.auth.views.login = log_auth_failures('Login')(
                django.contrib.auth.views.login)
