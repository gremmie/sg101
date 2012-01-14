from fabric.api import cd, run

PYTHON = '/home/var/django-sites/virtualenvs/sg101/bin/python'
WC_DIR = '/home/var/django-sites/virtualenvs/sg101/sg101'
PROJ_DIR = WC_DIR + '/gpp'

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
        '--settings=settings.production --noinput') % PYTHON

    with cd(PROJ_DIR):
        run(cmd)


def touch():
    """
    Touches the wsgi file to reload the Python code.

    """
    with cd(PROJ_DIR):
        run('touch apache/sg101.wsgi')
