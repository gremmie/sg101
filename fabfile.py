from fabric.api import cd, run

PYTHON = '/svr/django-sites/sg101/bin/python'
PROJ_DIR = '/svr/django-sites/sg101/sg101'

def update():
    """
    Runs hg pull --update to pull changes and update to them.

    """
    with cd(PROJ_DIR):
        run('hg pull --update')


def collectstatic():
    """
    Runs the staticfiles collectstatic command to deploy static assets.

    """
    cmd = ('%s manage.py collectstatic '
        '--settings=sg101.settings.production --noinput') % PYTHON

    with cd(PROJ_DIR):
        run(cmd)


def touch():
    """
    Touches the wsgi file to reload the Python code.

    """
    with cd(PROJ_DIR):
        run('touch ./sg101/apache/sg101.wsgi')
