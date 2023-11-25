#!/usr/bin/env python3

import os
import rumps
import subprocess
import sys
import time
from enum import Enum


shortcut_name = 'macos-focus-mode'

class FocusStatus(Enum):
    ON = 'on'
    OFF = 'off'


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
    def check_shortcut_installed(self) -> None:
        shortcuts = subprocess.run(['shortcuts','list'], capture_output=True, text=True).stdout.split('\n')
        if shortcut_name in shortcuts:
            return
        else:
            raise Exception("Shortcut not installed. Please see Alfred docs for instructions.")


    def set_dnd(self, status: FocusStatus, length: int=30) -> None:
        if status == FocusStatus.ON:
            shortcut_cmd = f'shortcuts run {shortcut_name} <<< "on {length}"'
        else:
            shortcut_cmd = f'shortcuts run {shortcut_name} <<< "off"'

        subprocess.run(shortcut_cmd, shell=True)


    # Decided to use osascript because restarting dock will launch all the app windows you have minimized
    def toggle_dock(self) -> None:
        subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to set autohide of dock preferences to not (autohide of dock preferences)']
        )


    def enable_focus(self, length: int) -> None:
        """Set Focus for X minutes"""
        self.check_shortcut_installed()

        self.set_dnd(FocusStatus.ON, length)
        self.toggle_dock()


    def disable_focus(self, terminate: bool=False) -> None:
        # This is for terminating focus before time is up
        if terminate:
            pass
        else:
            sys.exit('Focus does not appear to be running')

        self.set_dnd('off')
        self.toggle_dock()


if __name__ == '__main__':
    focus_command()