#!/usr/bin/env python3
from __future__ import annotations  # Enables automatic forward references
import os
import rumps
import subprocess
from enum import Enum


shortcut_name = 'alfred-focus-mode'
                       
class FocusState(Enum):
    ON = 'on'
    OFF = 'off'


def set_dnd(status: FocusState, length: int):
    if status == FocusState.ON:
        shortcut_cmd = f'shortcuts run {shortcut_name} <<< "on {length}"'
    else:
        shortcut_cmd = f'shortcuts run {shortcut_name} <<< "off"'

    subprocess.run(shortcut_cmd, shell=True)


# Decided to use osascript because restarting dock will launch all the app windows you have minimized
def toggle_dock():
    subprocess.run(
        ['osascript', '-e', 'tell application "System Events" to set autohide of dock preferences to not (autohide of dock preferences)']
    )


def enable_focus(length: int):
    set_dnd(FocusState.ON, length)
    toggle_dock()


def disable_focus():
    set_dnd(FocusState.OFF, 0)
    toggle_dock()


class FocusTimer:
    def __init__(self, app: Alfred):
        self.duration = None
        self.remaining_time = None
        self.time_left_msg = rumps.MenuItem('Time Left')
        self.end_focus = rumps.MenuItem('End Focus', callback=self.stop)
        self.is_running = False
        self.timer = None
        self.app = app

    
    def start(self, duration: int):
        self.duration = duration
        self.remaining_time = duration
        if self.is_running:
            return # Focus already running
        
        self.is_running = True
        enable_focus(duration)
        self.app.disable_menu_items()
        self.timer = rumps.Timer(self.run_focus, 1)
        self.timer.start()
        self.app.menu.insert_after('Focus', self.end_focus)
        self.app.menu.insert_after('End Focus', self.time_left_msg)

        
    def stop(self, sender=None):
        if self.timer:
            self.timer.stop()

        self.is_running = False
        disable_focus()
        del self.app.menu['Time Left']
        del self.app.menu['End Focus']
        self.app.enable_menu_items()
        

    def run_focus(self, sender):
        self.remaining_time -= 1
        mins, secs = divmod(self.remaining_time, 60)

        if self.remaining_time <= 0:
            self.stop()

        if (mins <= 0) & (secs >= 0):
            self.time_left_msg.title = f'Time Left: < 1 min'
        else:
            self.time_left_msg.title = f'Time Left: {mins} min'


class Alfred(rumps.App):
    def __init__(self):
        super(Alfred, self).__init__('Alfred', icon='assets/alfred-assist.icns')
        # rumps.debug_mode(True)

        # Make sure the shortcut is installed
        self.check_shortcut_installed()
        if not self.check_shortcut_installed():
            self.menu = [
                rumps.MenuItem('Install Focus Shortcut', callback=self.install_shortcut)
            ]
        else:
            self.setup_menu()
    
    
    def setup_menu(self):
        self.focus_lengths = [1, 5, 10, 15, None, 20, 25, 30, 35, None, 40, 45, 50, 55, None, 60, 90]
        self.focus_options = []
        
        for length in self.focus_lengths:
            if length:
                new_item = rumps.MenuItem(f'{length} min', callback=None)
                new_item.length = length
                new_item.set_callback(lambda _, length=new_item.length: FocusTimer(self).start(length * 60))
                self.focus_options.append(new_item)
            else:
                self.focus_options.append(None)

        self.focus_submenu = [*self.focus_options]

        self.menu = [
            {'Focus': self.focus_submenu},
        ]


    def disable_menu_items(self):
        """Disable focus menu items while a focus session is running."""
        for item in self.focus_options:
            if isinstance(item, rumps.MenuItem):
                item.set_callback(None)


    def enable_menu_items(self):
        """Re-enable focus menu items when the session ends."""
        for item in self.focus_options:
            if isinstance(item, rumps.MenuItem):
                length = int(item.title.split()[0])
                item.set_callback(lambda _, length=length: FocusTimer(self).start(length * 60))  # `state=False` makes it clickable again
            
        
    # Make sure the short cut is installed, have to use this method for osx 13
    def check_shortcut_installed(self):
        shortcuts = subprocess.run(['shortcuts','list'], capture_output=True).stdout.decode('ascii', 'ignore').split('\n')
        return True if shortcut_name in shortcuts else False
        

    # Install Focus Shortcut
    def install_shortcut(self, _):
        rumps.alert(title='Alfred Assist', message='Focus Shortcut not installed. Click "Add Shortcut" when the window pops up and then restart Alfred Assist.', ok='OK', cancel=None)
        subprocess.run(['open', f'assets/{shortcut_name}.shortcut'])


if __name__ == "__main__":
    Alfred().run()
