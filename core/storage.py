"""
Static file storage for production.

"""
from django.contrib.staticfiles import storage


class ManifestStaticFilesStorage(storage.ManifestStaticFilesStorage):
    """Django's manifest storage, with import specifiers in JavaScript modules
    rewritten to hashed names as well.

    Without this, a hashed module would import its siblings by their plain
    names, which are cached on a different lifetime, and a deploy could leave a
    browser running a new module against an old one.

    Django rewrites `import … from '…'` and `export … from '…'` only when a
    semicolon ends the statement. Without one, the specifier keeps its plain
    name and nothing fails; core/tests/test_storage.py checks the site's
    modules for that. (If another `from` statement follows, collectstatic
    fails instead, naming a file that does not exist.)
    """
    support_js_module_import_aggregation = True
