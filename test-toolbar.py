#!/usr/bin/env python3

import os
import rumps
import subprocess
from enum import Enum


home_dir = os.getenv('HOME')
shortcut_name = 'macos-focus-mode'


class FocusState(Enum):
    ON = 'on'
    OFF = 'off'


class Alfred(rumps.App):
    def __init__(self):
        super(Alfred, self).__init__('Alfred', icon='assets/alfred_icon.png')

        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()
        self.timer.count = 0

        focus_lengths = [1, 5, 10, 15, 30, 45, 60, 90]
        self.end_focus = rumps.MenuItem('End Focus', callback=self.disable_focus)
        self.focus_options = [rumps.MenuItem(f'{length} min', callback=self.enable_focus) for length in focus_lengths]

        self.menu = [
            {'Focus': [*self.focus_options, None, self.end_focus]},
        ]


    # Make sure the short cut is installed, have to use this method for osx 13
    def check_shortcut_installed(self):
        pass


    def on_tick(self, sender):
        # time_left = sender.end - sender.count
        # mins, secs = divmod(time_left, 60)
        sender.count += 1

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


    def disable_focus(self, sender=None):
        self.set_dnd(FocusState.OFF, 0)
        self.timer.stop()
        self.toggle_dock()
        self.timer.count = 0 
        for item in self.focus_options:
            item.set_callback(self.enable_focus)


if __name__ == "__main__":
    Alfred().run()