#!/usr/bin/env python3

import os
import rumps
import subprocess
from enum import Enum


shortcut_name = 'alfred-focus-mode'


class FocusState(Enum):
    ON = 'on'
    OFF = 'off'

class PomodoroState(Enum):
    ON = 'on'
    OFF = 'off'


class AlfredTimer(rumps.Timer):
    def __init__(self, callback, interval):
        super(AlfredTimer, self).__init__(callback, interval)
        self.stop()
        self.count = 0
        self.end = 0


class Alfred(rumps.App):
    def __init__(self):
        super(Alfred, self).__init__('Alfred', icon='assets/alfred-assist.icns')
        # rumps.debug_mode(True)

        self.timer = AlfredTimer(None, 1)
        self.pomodoro_state = PomodoroState.OFF
        self.pomodoro_session_count = 0

        self.FocusMode = FocusMode(self.timer, self)

        # Make sure the shortcut is installed
        self.check_shortcut_installed()
        if not self.check_shortcut_installed():
            self.menu = [
                rumps.MenuItem('Install Focus Shortcut', callback=self.install_shortcut)
            ]
        else:
            focus_lengths = [1, 5, 10, 15, None, 20, 25, 30, 35, None, 40, 45, 50, 55, None, 60, 90]
            self.end_focus = rumps.MenuItem('End Focus', callback=None)
            self.focus_options = [rumps.MenuItem(f'{length} min', callback=lambda _, length=length: self.FocusMode.enable(length)) if length else None for length in focus_lengths]

            self.time_left = rumps.MenuItem('Time Left: 0:00')
            self.time_left.hidden = True
            
            pomodoro_options = [
                rumps.MenuItem('Start', callback=None),
                rumps.MenuItem('End', callback=None),
                rumps.MenuItem('Set', callback=self.set_pomodoro),
            ]

            self.focus_submenu = [*self.focus_options, None, self.end_focus]

            self.menu = [
                {'Focus': self.focus_submenu},
                # {'Pomodoro': pomodoro_options},
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


    def enable_focus(self, length):
        """Set Focus for X minutes"""
        if type(length) == rumps.MenuItem:
            sleepy = int(length.title.split()[0])
        else:
            sleepy = length

        self.set_dnd(FocusState.ON, sleepy)
        self.toggle_dock()

        if self.pomodoro_state == PomodoroState.ON:
            for item in self.focus_options:
                item.set_callback(None) if item != None else None
        else:
            self.menu['Focus'] = None

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
            item.set_callback(self.enable_focus) if item != None else None
        
        self.time_left.hidden = True
        self.end_focus.set_callback(None)

    
    def set_pomodoro(self, sender):
        """Set Pomodoro"""
        pom_length = int(rumps.Window(
            message='Set Session Length', 
            title='Pomodoro Length', 
            default_text='25', 
            dimensions=(50,20), 
            ok='Set', 
            cancel='Cancel').run().text)
        
        pom_sessions = int(rumps.Window(
            message='Set Number of Sessions', 
            title='Pomodoro Sessions', 
            default_text='5', 
            dimensions=(50,20), 
            ok='Set', 
            cancel='Cancel').run().text)
        
        pom_break = int(rumps.Window(
            message='Set Break Length', 
            title='Pomodoro Break', 
            default_text='10', 
            dimensions=(50,20), 
            ok='Set', 
            cancel='Cancel').run().text)
        
        if (pom_length > 0) & (pom_sessions > 0) & (pom_break > 0):
            self.pomodoro_state = PomodoroState.ON
            self.enable_focus(pom_length)





            
class Mode:
    def __init__(self, timer: AlfredTimer):
        self.timer = timer


    def enable_focus(self, length):
        """Set Focus for X minutes"""
        sleepy = length
        self.set_dnd(FocusState.ON, sleepy)
        self.toggle_dock()
        self.timer.end = sleepy * 60
        self.timer.start()


    def disable_focus(self):
        self.set_dnd(FocusState.OFF, 0)
        self.timer.stop()
        self.toggle_dock()
        self.timer.count = 0


    def set_dnd(self, status: FocusState, length: int):
        if status == FocusState.ON:
            shortcut_cmd = f'shortcuts run {shortcut_name} <<< "on {length}"'
        else:
            shortcut_cmd = f'shortcuts run {shortcut_name} <<< "off"'

        subprocess.run(shortcut_cmd, shell=True)


    def toggle_dock(self):
        subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to set autohide of dock preferences to not (autohide of dock preferences)']
        )


class FocusMode(Mode):
    def __init__(self, timer: AlfredTimer, alfred: Alfred):
        super().__init__(timer)
        self.alfred = alfred
        self.timer.set_callback(self.on_tick)
        self.focus_options_enabled = self.alfred.focus_options

    
    def enable(self, length):
        for item in self.alfred.focus_options:
            item.set_callback(None) if item != None else None
        self.enable_focus(length)
        self.alfred.time_left.hidden = False
        self.alfred.end_focus.set_callback(self.disable)


    def disable(self, sender=None):
        self.disable_focus()
        self.alfred.time_left.hidden = True
        self.alfred.end_focus.set_callback(None)
        self.alfred.focus_options = self.focus_options_enabled


    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins, secs = divmod(time_left, 60)
        sender.count += 1
        if (mins <= 0) & (secs >= 0):
            self.alfred.time_left.title = f'Time Left: < 1 min'
        else:
            self.alfred.time_left.title = f'Time Left: {mins} min'

        if sender.count == sender.end:
            self.disable()


class PomodoroMode:
    pass        


if __name__ == "__main__":
    Alfred().run()
