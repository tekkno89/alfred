import click
import os
import rumps
import sys
import subprocess
import time
from datetime import datetime


home_dir = os.getenv('HOME')
pid_file = '/tmp/alfred_focus.pid'
shortcut_name = 'macos-focus-mode'

class Alfred(rumps.App):
    def __init__(self):
        super(Alfred, self).__init__('Alfred', icon='alfred_icon.png')
        self.menu = [
            ('Focus',[
                rumps.MenuItem('1 min', callback=self.enable_focus,),
                rumps.MenuItem('10 min', callback=self.enable_focus),
                rumps.MenuItem('15 min', callback=self.enable_focus),
                rumps.MenuItem('30 min', callback=self.enable_focus) 
            ])
        ]

    # Make sure the short cut is installed, have to use this method for osx 13
    def check_shortcut_installed(self):
        pass


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
        if isinstance(length, rumps.MenuItem):
            sleepy = int(length.title.split()[0])
        else:
            sleepy = int(length)

        self.set_dnd('on', sleepy)
        self.toggle_dock()
        pid = os.fork()

        if pid == 0:
            self.focus_daemon(sleepy, length)
        elif pid > 0:
            click.echo(f'Focus set for {sleepy} minute(s)')
            self.track_focus_process(pid)
            self.menu['Focus'][length.title].set_callback(None)


    def disable_focus(self, terminate=False):
        # This is for terminating focus before time is up
        if terminate:
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as file:
                    pid = file.read()
                os.kill(int(pid), 9)
                os.remove(pid_file)
            else:
                sys.exit('Focus does not appear to be running')

        self.set_dnd('off')
        self.toggle_dock()


    def focus_daemon(self, min, menu_item):
        time.sleep(min * 60)
        self.disable_focus()


    def track_focus_process(self, pid):
        with open(pid_file, 'w') as file:
            file.write(str(pid))


    # app = rumps.App('Alfred', icon='alfred_icon.png')
    # quit_button = rumps.MenuItem('Quit')
    # app.menu = [
    #     ('Focus', 
    #         [rumps.MenuItem('5 min', callback=enable_focus), '10 min', '30 min']), 
    #     'TBD'
    # ]

if __name__ == "__main__":
    Alfred().run()