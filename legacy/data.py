"""
Misc data for the legacy management commands.

"""

# Over time various users asked me to change their username. The legacy site
# rarely stored foreign keys to users; instead it stored the name of the user
# at the time. This dictionary contains mappings from old usernames to new
# usernames.

KNOWN_USERNAME_CHANGES = {
    'cavefishbutchdelux': 'butchdelux',
    'findicator1': 'WaveOhhh',
    'tikimania': 'Tikitena',
    'sandyfeet': 'RickRhoades',
    'crumb': 'crumble',
    'allenbridgewater': 'Outerwave_Allen',
    'reddtyde': 'Redd_Tyde',
    'fendershowman63': 'Abe',
    'hearteater': 'JoshHeartless',
    'surfdaddy': 'zzero',
    'frisbie': 'zzero',
    'retroactivegammarays': 'Retroactive_Taj',
    'mrrebel': 'Eddie_Bertrand',
    'doublecoil': 'Showman',
    'tsunami_tom': 'TomH',
    'davidj': 'davidphantomatic',
    'svd': 'Bilge_Rat',
    'dave_ledude': 'DaveF',
}

