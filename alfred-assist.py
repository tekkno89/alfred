#!/usr/bin/env python3

import os
import rumps
import subprocess
from enum import Enum


shortcut_name = 'alfred-focus-mode'


class FocusState(Enum):
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

        self.focus_timer = AlfredTimer(None, 1)
        self.pomodoro_timer = AlfredTimer(None, 1)
        self.focus_lengths = [1, 5, 10, 15, None, 20, 25, 30, 35, None, 40, 45, 50, 55, None, 60, 90]
        self.focus_options = []
        self.time_left = rumps.MenuItem('Time Left: 0:00')
        self.break_left = rumps.MenuItem('Break Left: 0:00')
        self.sessions_left = rumps.MenuItem('Sessions Left: 0')
        self.time_left.hidden = True
        self.break_left.hidden = True
        self.sessions_left.hidden = True

        # Make sure the shortcut is installed
        self.check_shortcut_installed()
        
        if not self.check_shortcut_installed():
            self.menu = [
                rumps.MenuItem('Install Focus Shortcut', callback=self.install_shortcut)
            ]
        else:
            self.FocusMode = FocusMode(self.focus_timer, self)
            self.PomodoroMode = PomodoroMode(self.pomodoro_timer, self)

            for length in self.focus_lengths:
                if length:
                    new_item = rumps.MenuItem(f'{length} min', callback=None)
                    new_item.length = length
                    new_item.set_callback(lambda _, length=new_item.length: self.FocusMode.enable(length))
                    self.focus_options.append(new_item)
                else:
                    self.focus_options.append(None)

            self.end_focus = rumps.MenuItem('End Focus', callback=None)
            self.focus_submenu = [*self.focus_options, None, self.end_focus]
            
            self.pomodoro_start = rumps.MenuItem('Start', callback=self.PomodoroMode.enable)
            self.pomodoro_end = rumps.MenuItem('End', callback=None)
            pomodoro_options = [
                self.pomodoro_start,
                self.pomodoro_end
            ]

            self.menu = [
                {'Focus': self.focus_submenu},
                {'Pomodoro': pomodoro_options},
                self.time_left,
                self.break_left,
                self.sessions_left
            ]
            
        
    # Make sure the short cut is installed, have to use this method for osx 13
    def check_shortcut_installed(self):
        shortcuts = subprocess.run(['shortcuts','list'], capture_output=True).stdout.decode('ascii', 'ignore').split('\n')
        return True if shortcut_name in shortcuts else False
        

    # Install Focus Shortcut
    def install_shortcut(self, _):
        rumps.alert(title='Alfred Assist', message='Focus Shortcut not installed. Click "Add Shortcut" when the window pops up and then restart Alfred Assist.', ok='OK', cancel=None)
        subprocess.run(['open', f'assets/{shortcut_name}.shortcut'])


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

    
    def enable(self, length):
        self.enable_focus(length)
        self.alfred.time_left.hidden = False
        self.alfred.end_focus.set_callback(self.disable)
        for item in self.alfred.focus_options:
            item.set_callback(None) if item is not None else None


    def disable(self, sender=None):
        self.disable_focus()
        self.alfred.time_left.hidden = True
        self.alfred.end_focus.set_callback(None)
        for item in self.alfred.focus_options:
            item.set_callback(callback=lambda _, length=item.length: self.enable(length)) if item is not None else None


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


class PomodoroMode(Mode):
    def __init__(self, timer: AlfredTimer, alfred: Alfred):
        super().__init__(timer)
        self.alfred = alfred
        self.timer.set_callback(self.on_tick)
        self.sessions_left = None


    def enable(self, _):
        # Set Pomodoro
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
            self.enable_focus(pom_length)
            self.sessions_left = pom_sessions
            self.alfred.time_left.hidden = False
            self.alfred.sessions_left.title = f'Sessions Left: {self.sessions_left}'
            self.alfred.sessions_left.hidden = False
            self.alfred.pomodoro_end.set_callback(self.disable)


    def disable(self, sender=None):
        self.disable_focus()
        self.alfred.time_left.hidden = True
        self.alfred.break_left.hidden = True
        self.alfred.sessions_left.hidden = True
        self.alfred.pomodoro_end.set_callback(None)


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
        


if __name__ == "__main__":
    Alfred().run()
