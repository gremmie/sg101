"""Authentication backends for the accounts application."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Value
from django.db.models.functions import Lower


class CaseInsensitiveModelBackend(ModelBackend):
    """ModelBackend, matching the username without regard to case.

    MySQL's case-insensitive collation made the old site's login match
    `kojack` to `Kojack`. Django's own backend matches the name exactly, and
    PostgreSQL compares exactly, so a member typing their name in another case
    was told their password was wrong.

    Only the lookup differs. The name cannot match two accounts: the unique
    index on LOWER(username), from accounts 0002, forbids it. The lookup is
    written against LOWER rather than with __iexact, which compiles to UPPER()
    on PostgreSQL and so could not use that index.
    """

    def _user_queryset(self, username):
        UserModel = get_user_model()
        return UserModel._default_manager.alias(
            username_lower=Lower(UserModel.USERNAME_FIELD),
        ).filter(username_lower=Lower(Value(username)))

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = self._user_queryset(username).get()
        except UserModel.DoesNotExist:
            # As ModelBackend does: run the hasher once anyway, so a missing
            # account takes as long to refuse as a wrong password (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None

    async def aauthenticate(self, request, username=None, password=None,
                            **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = await self._user_queryset(username).aget()
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            if (await user.acheck_password(password)
                    and self.user_can_authenticate(user)):
                return user
        return None
