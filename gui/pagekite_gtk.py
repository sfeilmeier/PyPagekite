#!/usr/bin/env python
import os
import gtk

class PageKiteStatusIcon(gtk.StatusIcon):
  MENU = '''
      <ui>
       <menubar name="Menubar">
        <menu action="Menu">
         <menuitem action="OpenLog"/>
         <menuitem action="OpenWebUi"/>
         <menuitem action="About"/>
         <separator/>
         <menuitem action="QuickShare"/>
         <menuitem action="KiteList"/>
         <separator/>
         <menuitem action="SignUp"/>
         <menuitem action="QuotaDisplay"/>
         <menuitem action="GetQuota"/>
         <separator/>
         <menuitem action="Preferences"/>
         <menuitem action="VerboseLog"/>
         <menuitem action="EnablePageKite"/>
         <menuitem action="Quit"/>
        </menu>
       </menubar>
      </ui>
  '''

  def __init__(self):
    gtk.StatusIcon.__init__(self)
    self.manager = gtk.UIManager()
    self.set_from_stock(gtk.STOCK_FIND)
    self.set_tooltip('PageKite')

    self.create_menu()

    self.connect('activate', self.on_activate)
    self.connect('popup-menu', self.on_popup_menu)
    self.set_visible(True)

  def create_menu(self):
    ag = gtk.ActionGroup('Actions')
    ag.add_actions([
      ('Menu',  None, 'Menu'),

      ('OpenLog', None, 'Show PageKite _Log',
                  None, 'Display PageKite Event Log', self.on_activate),
      ('OpenWebUi',  None, 'Open _PageKite Status',
                     None, '', self.on_stub),
      ('About', gtk.STOCK_ABOUT, '_About...',
                None, '_About PageKite', self.on_about),

      ('QuickShare',  None, '_Quick Sharing (0.0MB)',
                     None, '', self.on_stub),
      ('KiteList',  None, 'Your _Kites (3)',
                     None, '', self.on_stub),

      ('SignUp',  None, 'Sign up at PageKite.net',
                     None, '', self.on_stub),
      ('QuotaDisplay',  None, 'XX.YY GB of Quota left',
                     None, '', self.on_stub),
      ('GetQuota',  None, 'Get _More Quota...',
                     None, '', self.on_stub),


      ('Preferences', gtk.STOCK_PREFERENCES, '_Preferences...',
                      None, 'Change MetaTracker preferences',
                      self.on_preferences),
      ('VerboseLog',  None, 'Verbose Logging',
                     None, '', self.on_stub),
      ('EnablePageKite',  None, 'Enable PageKite',
                     None, '', self.on_stub),
      ('Quit',  None, '_Quit PageKite',
                None, '', self.on_stub),
    ])

    self.manager.insert_action_group(ag, 0)
    self.manager.add_ui_from_string(self.MENU)

    # Hide stuff that shouldn't be active right now
    self.manager.get_widget('/Menubar/Menu/SignUp').hide()

    self.menu = self.manager.get_widget('/Menubar/Menu/About').props.parent


  def on_activate(self, data):
    print 'Activated'

  def on_popup_menu(self, status, button, time):
    self.menu.popup(None, None, None, button, time)

  def on_preferences(self, data):
    print 'preferences'

  def on_stub(self, data):
    print 'Stub'

  def on_about(self, data):
    dialog = gtk.AboutDialog()
    dialog.set_name('PageKite')
    dialog.set_version('0.5.0')
    dialog.set_comments('A desktop indexing and search tool')
    dialog.set_website('www.freedesktop.org/Tracker')
    dialog.run()
    dialog.destroy()

if __name__ == '__main__':
  PageKiteStatusIcon()
  gtk.main()

