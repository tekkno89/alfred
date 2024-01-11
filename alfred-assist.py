#!/usr/bin/env python3

import os
import rumps
import subprocess
from enum import Enum


home_dir = os.getenv('HOME')
shortcut_name = 'alfred-focus-mode'


class FocusState(Enum):
    ON = 'on'
    OFF = 'off'


class Alfred(rumps.App):
    def __init__(self):
        super(Alfred, self).__init__('Alfred', icon='assets/alfred-assist.icns')
        # rumps.debug_mode(True)

        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()
        self.timer.count = 0

        # Make sure the shortcut is installed
        self.check_shortcut_installed()
        if not self.check_shortcut_installed():
            self.menu = [
                rumps.MenuItem('Install Focus Shortcut', callback=self.install_shortcut)
            ]
        else:
            focus_lengths = [1, 5, 10, 15, 30, 45, 60, 90]
            self.end_focus = rumps.MenuItem('End Focus', callback=None)
            self.focus_options = [rumps.MenuItem(f'{length} min', callback=self.enable_focus) for length in focus_lengths]
            self.time_left = rumps.MenuItem('Time Left: 0:00')
            self.time_left.hidden = True
            self.menu = [
                {'Focus': [*self.focus_options, None, self.end_focus]},
                self.time_left
            ]
            
        
    # Make sure the short cut is installed, have to use this method for osx 13
    def check_shortcut_installed(self):
        shortcuts = subprocess.run(['shortcuts','list'], capture_output=True).stdout.decode('ascii', 'ignore').split('\n')
        return True if shortcut_name in shortcuts else False
        

    # Install Focus Shortcut
    def install_shortcut(self, _):
        rumps.alert(title='Alfred Assist', message='Focus Shortcut not installed. Click "Add Shortcut" when the window pops up and then restart Alfred Assist.', ok='OK', cancel=None)
        subprocess.run(['open', f'assets/{shortcut_name}.shortcut'])


    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins, secs = divmod(time_left, 60)
        sender.count += 1
        if (mins <= 0) & (secs >= 0):
            self.time_left.title = f'Time Left: < 1 min'
        else:
            self.time_left.title = f'Time Left: {mins} min'

        if sender.count == sender.end:
            self.disable_focus()


    def set_dnd(self, status: FocusState, length: int):
        if status == FocusState.ON:
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
        self.set_dnd(FocusState.ON, sleepy)
        self.toggle_dock()

        for item in self.focus_options:
            item.set_callback(None)

        self.timer.end = sleepy * 60
        self.timer.start()
        self.time_left.hidden = False
        self.end_focus.set_callback(self.disable_focus)


    def disable_focus(self, sender=None):
        self.set_dnd(FocusState.OFF, 0)
        self.timer.stop()
        self.toggle_dock()
        self.timer.count = 0 
        for item in self.focus_options:
            item.set_callback(self.enable_focus)
        self.time_left.hidden = True
        self.end_focus.set_callback(None)


if __name__ == "__main__":
    Alfred().run()