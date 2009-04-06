'''This module adds a simple logging facility to the portal.
Applications can log information to a database table for debugging.
The logger is similar to the python logging module.
The verbosity of the logging is controlled via settings.GPP_LOG_LEVEL. 
'''

from settings import GPP_LOG_LEVEL
from core.models import DebugLog

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

def log(level, msg):
   if GPP_LOG_LEVEL <= level:
      log_item = DebugLog()
      log_item.level = level
      log_item.msg = msg
      log_item.save()

def debug(msg):
   log(DEBUG, msg)

def info(msg):
   log(INFO, msg)

def warning(msg):
   log(WARNING, msg)

def error(msg):
   log(WARNING, msg)

def critical(msg):
   log(WARNING, msg)
