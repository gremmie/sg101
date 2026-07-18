"""
Smoke tests for the whole management-command surface.

Management commands are easy to break silently during a framework upgrade: most
have no tests of their own, and the breakage -- a removed base class
(``NoArgsCommand``), a dropped ``optparse`` option API (``option_list`` /
``make_option``) -- happens at *import* or *parser-construction* time, long
before ``handle()`` ever runs. A green unit suite says nothing about a command
whose class body no longer imports.

These walk every registered command, import its class, and build its argument
parser (which runs ``add_arguments``), asserting the entire surface still loads.
Cheap insurance of the same kind as the admin changelist smoke tests -- and the
exact check that would have caught the batch of commands stranded on the removed
1.9-era APIs during the Django upgrade.
"""
from django.core.management import get_commands, load_command_class
from django.test import TestCase


class CommandSurfaceSmokeTests(TestCase):

    def test_command_registry_is_populated(self):
        # Guard against get_commands() silently returning (almost) nothing,
        # which would make the load test below vacuously pass.
        self.assertGreater(len(get_commands()), 20)

    def test_every_command_loads_and_builds_its_parser(self):
        failures = []
        for name, app_name in sorted(get_commands().items()):
            try:
                command = load_command_class(app_name, name)
                command.create_parser('manage.py', name)
            except Exception as e:
                failures.append('%s (%s): %s' % (name, app_name, e))

        self.assertEqual(failures, [],
                         msg='commands failed to load / build their parser: %s'
                             % '; '.join(failures))
