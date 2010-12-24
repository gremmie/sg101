"""
Misc data for the legacy management commands.

"""

# Over time various users asked me to change their username. The legacy site
# rarely stored foreign keys to users; instead it stored the name of the user
# at the time. This dictionary contains mappings from old usernames to new
# usernames.

KNOWN_USERNAME_CHANGES = {
    'cavefishbutchdelux': 'butchdelux',
    'Findicator1': 'WaveOhhh',
    'Tikimania': 'Tikitena',
    'sandyfeet': 'RickRhoades',
}

