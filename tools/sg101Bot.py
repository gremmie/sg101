#! /usr/bin/env python
"""sg101Bot.py

IRC Bot for SurfGuitar101.com's IRC server.
This bot watches who is in the given channel and updates a MySQL
database accordingly. The database is read by the website to display
who is in the channel.

Brian Neal <brian@surfguitar101.com>
"""

import re
import sys
import random
import logging
from optparse import OptionParser
import ConfigParser

import MySQLdb
import irclib
from daemon import Daemon

#irclib.DEBUG = True

class QuoteDb(object):
   """QuoteDb is a class that reads a quote file and provdes a random quote when asked"""

   def __init__(self, filename):
      random.seed()
      f = open(filename, 'r')
      self.quotes = []
      for line in f:
         self.quotes.append(line.strip())
      f.close()

   def get(self):
      return random.choice(self.quotes)
      

class Sg101Table(object):
   """Sg101Table class for abstracting the database table that is used to store who is in the channel"""
   
   def __init__(self, dbHost, dbName, dbUser, dbPassword, tableName):
      self.dbArgs = {'host' : dbHost, 'user' : dbUser, 'passwd' : dbPassword, 'db' : dbName}
      self.table = tableName
      self.dbRefCnt = 0

   def empty(self):
      self.__dbOpen()
      """empties the table of channel users"""
      logging.debug('emptying the table')
      self.cursor.execute('TRUNCATE TABLE ' + self.table)
      self.__dbClose()

   def add(self, nick):
      self.__dbOpen()
      """adds the nickname to the table"""
      logging.debug('adding to the table: ' + nick)
      self.cursor.execute("INSERT INTO " + self.table +
          " (name, last_update) VALUES (%s, NOW())", nick)
      self.__dbClose()

   def remove(self, nick):
      self.__dbOpen()
      """removes the nickname from the table"""
      logging.debug('removing from the table: ' + nick)
      self.cursor.execute("DELETE FROM " + self.table + " WHERE `name` = %s", nick)
      self.__dbClose()

   def set(self, nicks):
      self.__dbOpen()
      """empties and then adds all the nicknames in the nicks list to the table"""
      self.empty()
      logging.debug('setting the table: ' + ', '.join(nicks))
      for nick in nicks:
         self.add(nick)
      self.__dbClose()

   def __dbOpen(self):
      if self.dbRefCnt <= 0:
         self.connection = MySQLdb.connect(
            host = self.dbArgs['host'],
            user = self.dbArgs['user'],
            passwd = self.dbArgs['passwd'],
            db = self.dbArgs['db'])
         self.cursor = self.connection.cursor()
         self.dbRefCnt = 1
      else:
         self.dbRefCnt = self.dbRefCnt + 1

   def __dbClose(self):
      self.dbRefCnt = self.dbRefCnt - 1
      if self.dbRefCnt <= 0:
         self.cursor.close()
         self.connection.commit()
         self.connection.close()
         self.dbRefCnt = 0
      

class Sg101Bot(irclib.SimpleIRCClient):
   """Sg101Bot class for monitoring a given channel and updating a database table accordingly"""

   def __init__(self, channel, nickname, server, port, password, db, quotes, quoteMod = 5):
      """__init__ function for Sg101Bot"""

      irclib.SimpleIRCClient.__init__(self)
      self.channel = channel
      self.nickname = nickname
      self.server = server
      self.port = port
      self.password = password
      self.users = []
      self.db = db
      self.quotes = quotes
      self.quoteMod = quoteMod
      self.pingCount = 0;

   def start(self):
      """call this function to start the bot"""
      self.db.empty()
      self.__connect()
      irclib.SimpleIRCClient.start(self)

   def on_nicknameinuse(self, c, e):
      """called if nick is in use; attempts to change nick"""
      c.nick(c.get_nickname() + "_")

   def on_welcome(self, c, e):
      """called when welcomed to the IRC server; attempts to join channel"""
      c.join(self.channel)

   def on_namreply(self, c, e):
      """called when we hear a namreply; we scan the names and if different than our
      info of who is in the channel we update the database"""
      me = c.get_nickname()
      users = [re.sub('^[@\+]', '', u) for u in e.arguments()[2].split(' ') if u != me]
      users.sort()
      if (self.users != users):
         logging.debug('on_namreply: detecting user list difference')
         self.users = users
         self.db.set(users)
         self.__printUsers()

   def on_join(self, c, e):
      """called after we or someone else joins the channel; update our list of users and db"""
      nick = irclib.nm_to_n(e.source())
      if nick != c.get_nickname() and nick not in self.users:
         self.__addUser(nick)
         self.__printUsers()

   def on_part(self, c, e):
      """called after we or someone else parts the channel; update our list of users and db"""
      nick = irclib.nm_to_n(e.source())
      if nick != c.get_nickname():
         self.__delUser(nick)
         self.__printUsers()

   def on_kick(self, c, e):
      """called after someone is kicked; update our list of users and db"""
      nick = e.arguments()[0]
      if nick != c.get_nickname():
         self.__delUser(nick)
         self.__printUsers()

   def on_quit(self, c, e):
      """called after someone quits; update our list of users and db"""
      nick = irclib.nm_to_n(e.source())
      if nick != c.get_nickname():
         self.__delUser(nick)
         self.__printUsers()

   def on_ping(self, c, e):
      """called when we are pinged; we use this opportunity to ask who is in the channel via NAMES"""
      c.names()
      self.pingCount = self.pingCount + 1
      if (self.quoteMod > 0) and len(self.users) > 0 and (self.pingCount % self.quoteMod) == 0:
         c.privmsg(self.channel, self.quotes.get())

   def on_privmsg(self, c, e):
      self.doCommand(e, e.arguments()[0], e.source())

   def on_pubmsg(self, c, e):
      a = e.arguments()[0].split(':', 1)
      if len(a) > 1 and irclib.irc_lower(a[0]) == irclib.irc_lower(c.get_nickname()):
         self.doCommand(e, a[1].strip(), e.target())

   def on_disconnect(self, c, e):
      logging.critical('received on_disconnect()')
      logging.debug('scheduling a routine in 30 secs')
      self.users = []
      self.db.empty()
      self.connection.execute_delayed(30, self.__connectedChecker)

   def __connectedChecker():
      logging.debug('__connectedChecker()')
      if not self.connection.is_connected():
         logging.debug('rescheduling __connectedChecker in 30 secs')
         self.connection.execute_delayed(30, self._connected_checker)
         self.__connect()


   def doCommand(self, e, cmd, reply):
      if cmd == 'yow':
         self.connection.privmsg(reply, self.quotes.get())

   def __connect(self):
      """our internal connect function"""
      self.connect(self.server,
                   self.port,
                   self.nickname,
                   self.password)

   def __printUsers(self):
      """internal print users command"""
      msg = 'My users are: (' + ', '.join(self.users) +  ')'
      logging.debug(msg)

   def __addUser(self, nick):
      """adds a user to our list and db"""
      self.users.append(nick)
      self.users.sort()
      self.db.add(nick)

   def __delUser(self, nick):
      """removes a user from our list and db"""
      if nick in self.users:
         self.users.remove(nick)
      self.db.remove(nick)


class BotDaemon(Daemon):
    def __init__(self, filename, options, db_config):
        Daemon.__init__(self, filename)
        self.options = options
        self.db_config = db_config

    def run(self):
        logging.basicConfig(level = logging.DEBUG,
                           format = '%(asctime)s %(levelname)s %(message)s',
                           filename = '/home/brian/irc/sg101Bot.log',
                           filemode = 'w')
        logging.info('sg101Bot starting')

        server = self.options.server
        port = self.options.port
        channel = self.options.channel
        nickname = self.options.nick
        password = self.options.password

        try:
          quotes = QuoteDb('/home/brian/irc/zippy.txt')
          db = Sg101Table(self.db_config['host'],
                  self.db_config['database'],
                  self.db_config['user'],
                  self.db_config['password'],
                  self.db_config['table'])
          bot = Sg101Bot(channel, nickname, server, port, password, db, quotes, 0)
          bot.start()
        except MySQLdb.OperationalError, message:
          logging.exception('MySQLdb.OperationalError: %d %s' % (message[0], message[1]))
        except MySQLdb.ProgrammingError, message:
          logging.exception('MySQLdb.ProgrammingError: %d %s' % (message[0], message[1]))
        except:
           print "Got an exception:", sys.exc_info()[0]
           logging.exception('Exception received ' + str(sys.exc_info()))

        logging.info('sg101Bot ending')

if __name__ == "__main__":
    parser = OptionParser(usage='usage: %prog [options] start|stop|restart',
         description="""\
    SG101 IRC Bot. Monitors who is in the specified channel and
    updates a database table accordingly for display by the website.
    """)

    parser.add_option("-s", "--server", default="localhost",
         help="server address")
    parser.add_option("-p", "--port", type="int", default=6667,
         help="port number")
    parser.add_option("-c", "--channel", default="#ShallowEnd",
         help="channel name")
    parser.add_option("-n", "--nick", default="bot",
         help="bot nickname")
    parser.add_option("-w", "--password", default="morereverb",
         help="channel password")
    parser.add_option("-q", "--quote", default="/home/brian/irc/zippy.txt",
         help="Quote file")
    (options, args) = parser.parse_args()

    commands = ('start', 'stop', 'restart')
    if len(args) != 1 and args[0] not in commands:
        parser.print_help()
        sys.exit("Please provide a single command: start, stop, or restart.")

    config = ConfigParser.ConfigParser()
    config.read('/home/brian/irc/sg101Bot.ini')
    db_config = dict(config.items('Database'))

    daemon = BotDaemon('/tmp/sg101Bot.pid', options, db_config)
    cmd = args[0]
    if cmd == 'start':
        daemon.start()
    elif cmd == 'stop':
        daemon.stop()
    elif cmd == 'restart':
        daemon.restart()
