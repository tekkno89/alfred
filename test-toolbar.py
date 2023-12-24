import os
import rumps
import sys
import subprocess
import time
from datetime import datetime


home_dir = os.getenv('HOME')
shortcut_name = 'macos-focus-mode'

class Alfred(rumps.App):
    def __init__(self):
        super(Alfred, self).__init__('Alfred', icon='assets/alfred_icon.png')

        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()
        self.timer.count = 0

        self.menu = [
            ('Focus',[
                rumps.MenuItem('1 min', callback=self.enable_focus),
                rumps.MenuItem('10 min', callback=self.enable_focus),
                rumps.MenuItem('15 min', callback=self.enable_focus),
                rumps.MenuItem('30 min', callback=self.enable_focus) 
            ])
        ]

    # Make sure the short cut is installed, have to use this method for osx 13
    def check_shortcut_installed(self):
        pass


    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins, secs = divmod(time_left, 60)
        sender.count += 1

        if sender.count == sender.end:
            self.disable_focus()
            self.timer.stop()


    def set_dnd(self, status, length=30):
        if status == 'on':
            shortcut_cmd = f'shortcuts run {shortcut_name} <<< "on {length}"'
        else:
            shortcut_cmd = f'shortcuts run {shortcut_name} <<< "off"'

        subprocess.run(shortcut_cmd, shell=True)


    # Decided to use osascript because restarting dock will launch all the app windows you have minimized
    def toggle_dock(self):
        subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to set autohide of dock preferences to not (autohide of dock preferences)']
        )


    def enable_focus(self, length: rumps.MenuItem):
        """Set Focus for X minutes"""
        sleepy = int(length.title.split()[0])

        self.set_dnd('on', sleepy)
        self.toggle_dock()
        self.timer.end = sleepy * 60
        self.timer.start()


    def disable_focus(self):
        self.set_dnd('off')
        self.toggle_dock()


    # app = rumps.App('Alfred', icon='alfred_icon.png')
    # quit_button = rumps.MenuItem('Quit')
    # app.menu = [
    #     ('Focus', 
    #         [rumps.MenuItem('5 min', callback=enable_focus), '10 min', '30 min']), 
    #     'TBD'
    # ]

if __name__ == "__main__":
    Alfred().run()