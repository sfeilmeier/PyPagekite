#!/usr/bin/env python
import os
import gobject
import gtk
import sys
import socket
import threading
import time
import webbrowser
import xmlrpclib

import pagekite


ENABLE_SHARING = False

SERVICE_DOMAINS = [
  '.pagekite.me', '.pagekite.net', '.pagekite.us', '.pagekite.info'
]
URL_HOME     = ('https://pagekite.net/home/')
URL_SIGNUP   = ('https://pagekite.net/signup/')
URL_GETKITES = ('http://localhost:8000/signup/?do_login=1&more=kites'
                '&r=%s:%s/pagekite/new_kite/')
URL_GETQUOTA = ('http://localhost:8000/signup/?do_login=1&more=bw')

ICON_FILE_ACTIVE  = 'icons-127/pk-active.png'
ICON_FILE_TRAFFIC = 'icons-127/pk-traffic.png'
ICON_FILE_IDLE    = 'icons-127/pk-idle.png'


class PageKiteThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.pk = None
    self.alive = False
    self.stopped = False

  def IsRunning(self):
    return (self.pk and self.pk.IsRunning()) and True or False

  def IsStopping(self):
    return (self.IsRunning() and self.stopped) and True or False

  def Configure(self, pk):
    if self.stopped: raise KeyboardInterrupt('Quit')
    self.pk = pk
    try:
      return pagekite.Configure(pk)
    except pagekite.ConfigError, e:
      gobject.idle_add(sys.exit, 1)
      raise pagekite.ConfigError(e)

  def run(self):
    self.looping = True
    while self.looping:
      if self.stopped:
        time.sleep(1)
      else:
        self.alive = True
        pagekite.Main(pagekite.PageKite, lambda pk: self.Configure(pk))
        while self.pk and self.pk.IsRunning(): time.sleep(0.2)
        self.pk = None
        self.alive = False

  def start_pk(self):
    self.stopped = False

  def stop_pk(self):
    self.stopped = True
    if self.pk: self.pk.looping = False

  def restart(self):
    if self.pk: self.pk.looping = False

  def toggle(self, data):
    if self.stopped:
      self.start_pk()
    else:
      self.stop_pk()

  def quit(self):
    self.looping = False
    self.stop_pk()


class PageKiteStatusIcon(gtk.StatusIcon):
  MENU = '''
      <ui>
       <menubar name="Menubar">
        <menu action="Menu">
         <menuitem action="OpenLog"/>
         <menuitem action="OpenWebUi"/>
         <menuitem action="About"/>
        <separator/>
         <menu action="QuickShare">
          <menuitem action="QuickShareClipBoard"/>
          <menuitem action="QuickSharePath"/>
          <menuitem action="QuickShareScreen"/>
         <separator/>
          <menuitem action="QuickShareHistory"/>
         <separator/>
          <menuitem action="QuickShareMirroring"/>
          <menuitem action="QuickShareEnabled"/>
         </menu>
         <menu action="KiteList">
          <menuitem action="KiteListEmpty"/>
         </menu>
        <separator/>
         <menuitem action="QuotaDisplay"/>
         <menuitem action="GetQuota"/>
        <separator/>
         <menuitem action="VerboseLog"/>
         <menuitem action="EnablePageKite"/>
         <menuitem action="Quit"/>
        </menu>
       </menubar>
      </ui>
  '''

  def __init__(self, pkThread):
    gtk.StatusIcon.__init__(self)

    self.pkThread = pkThread
    self.manager = gtk.UIManager()

    self.create_menu()
    self.set_tooltip('PageKite')

    self.icon_file = ICON_FILE_IDLE
    self.set_from_file(self.icon_file)

    self.connect('activate', self.on_activate)
    self.connect('popup-menu', self.on_popup_menu)
    gobject.timeout_add_seconds(1, self.on_tick)

    self.set_visible(True)
    self.pkThread.start()

  def create_menu(self):
    ag = gtk.ActionGroup('Actions')
    ag.add_actions([
      ('Menu',  None, 'Menu'),

      ('OpenLog', None, 'Show PageKite _Log', None, 'Display PageKite event log', self.on_stub),
      ('OpenWebUi', None, 'Open _PageKite Status', None, 'Open PageKite status in your Browser', self.on_stub),
      ('About', gtk.STOCK_ABOUT, 'About', None, 'About PageKite', self.on_about),

      ('QuickShare', None, '_Quick Sharing (0.0MB)', None, 'Quickly share work and files over the web'),
       ('QuickShareClipBoard', None, 'Paste To Web', None, None, self.on_stub),
       ('QuickSharePath', None, 'Share From Disk', None, None, self.on_stub),
       ('QuickShareScreen', None, 'Share Screenshot', None, None, self.on_stub),
       ('QuickShareHistory', None, 'History...', None, None, self.on_stub),
       ('QuickShareMirroring', None, 'Mirroring...', None, None, self.on_stub),
      ('KiteList', None, 'Your _Kites (3)', None, 'Your active PageKites'),
       ('KiteListEmpty', None, '<nothing>', None, None, self.on_stub),

      ('QuotaDisplay', None, 'XX.YY GB of Quota left'),
      ('GetQuota', None, 'Get _More Quota...', None, 'Get more Quota from PageKite.net', self.on_stub),

      ('Quit', None, '_Quit PageKite', None, 'Turn PageKite off completely', self.quit),
    ])
    ag.add_toggle_actions([
      ('QuickShareEnabled', None, '_Enable Sharing', None, None, self.on_stub, False),
      ('VerboseLog', None, 'Verbose Logging', None, 'Verbose logging facilitate troubleshooting.', self.on_stub, False),
      ('EnablePageKite', None, 'Enable PageKite', None, 'Enable or disable PageKite', self.pkThread.toggle, True),
    ])

    self.manager.insert_action_group(ag, 0)
    self.manager.add_ui_from_string(self.MENU)
    self.manager.get_widget('/Menubar/Menu/QuotaDisplay').set_sensitive(False)
    self.menu = self.manager.get_widget('/Menubar/Menu/About').props.parent

  def on_activate(self, data):
    self.show_menu(0, 0)
    return False

  def on_tick(self):
    old_if = self.icon_file

    if self.pkThread.stopped:
      self.icon_file = ICON_FILE_IDLE
      self.set_tooltip('PageKite (idle)')
    else:
      min_ts = '%x' % (time.time()-2)
      traffic = False
      for line in [l for l in pagekite.LOG if l['ts'] > min_ts]:
        # FIXME: Make this a little smarter? Detect on-going transfers?
        if 'FE' in line: traffic = True
        if 'is' in line: traffic = True
        if 'wrote' in line: traffic = True

      if traffic:
        self.icon_file = ICON_FILE_TRAFFIC
        self.set_tooltip('PageKite (active)')
      else:
        self.icon_file = ICON_FILE_ACTIVE
        self.set_tooltip('PageKite (active)')

    if self.icon_file != old_if: self.set_from_file(self.icon_file)
    return True

  def on_popup_menu(self, status, button, when):
    if self.menu.props.visible:
      self.menu.popdown()
    else:
      self.show_menu(button, when)
    return False

  def show_menu(self, button, when):
    w = self.manager.get_widget

    if not ENABLE_SHARING: w('/Menubar/Menu/QuickShare').hide()
       
    w('/Menubar/Menu/EnablePageKite').set_active(not self.pkThread.stopped)
    w('/Menubar/Menu/OpenLog').set_sensitive(not self.pkThread.stopped)
    w('/Menubar/Menu/OpenWebUi').set_sensitive(not self.pkThread.stopped)
    w('/Menubar/Menu/QuickShare').set_sensitive(not self.pkThread.stopped)
    w('/Menubar/Menu/KiteList').set_sensitive(not self.pkThread.stopped)
    if self.pkThread.stopped:
      w('/Menubar/Menu/QuotaDisplay').hide()
      w('/Menubar/Menu/GetQuota').hide()
    else:
      w('/Menubar/Menu/QuotaDisplay').show()
      w('/Menubar/Menu/GetQuota').show()

    self.menu.popup(None, None, None, button, when)

  def on_stub(self, data):
    print 'Stub'

  def on_about(self, data):
    dialog = gtk.AboutDialog()
    dialog.set_name('PageKite')
    dialog.set_version(pagekite.APPVER)
    dialog.set_comments('PageKite is a tool for running personal servers, '
                        'sharing work and communicating over the WWW.')
    dialog.set_website(pagekite.WWWHOME)
    dialog.run()
    dialog.destroy()

  def quit(self, data):
    self.pkThread.quit()
    sys.exit(0)


if __name__ == '__main__':
  pkt = PageKiteThread()
  try:
    pksi = PageKiteStatusIcon(pkt)
    gobject.threads_init()
    gtk.main()
  except:
    pass
  pkt.quit()

