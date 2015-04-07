from django.contrib.messages.apps import MessagesConfig


# The Django messages app conflicts with our own messages app.
# Override the label to fix this.

class DjangoMessagesConfig(MessagesConfig):
    label = 'django_messages'
