#!/usr/bin/env python3

import os
import rumps
import subprocess
from enum import Enum


shortcut_name = 'alfred-focus-mode'


class FocusState(Enum):
    ON = 'on'
    OFF = 'off'


class FocusTimer(rumps.Timer):
    def __init__(self, callback, interval):
        super(FocusTimer, self).__init__(callback, interval)
        self.stop()
        self.count = 0
        self.end = 0


class Alfred(rumps.App):
    def __init__(self):
        super(Alfred, self).__init__('Alfred', icon='assets/alfred-assist.icns')
        # rumps.debug_mode(True)

        self.focus_timer = FocusTimer(None, 1)
        self.pomodoro_timer = FocusTimer(None, 1)
        self.focus_lengths = [1, 5, 10, 15, None, 20, 25, 30, 35, None, 40, 45, 50, 55, None, 60, 90]
        self.focus_options = []
        self.time_left = rumps.MenuItem('Time Left: 0:00')
        self.sessions_left = rumps.MenuItem('Sessions Left: 0')
        self.time_left.hidden = True
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
            
            self.pomodoro_start = rumps.MenuItem('Start', callback=self.PomodoroMode.init_pomodoro)
            self.pomodoro_end = rumps.MenuItem('End', callback=None)
            pomodoro_options = [
                self.pomodoro_start,
                self.pomodoro_end
            ]

            self.menu = [
                {'Focus': self.focus_submenu},
                {'Pomodoro': pomodoro_options},
                self.time_left,
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
    def __init__(self, timer: FocusTimer):
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
    def __init__(self, timer: FocusTimer, alfred: Alfred):
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
        self.timer.stop()
        self.disable_focus()
        self.alfred.time_left.hidden = True
        self.alfred.end_focus.set_callback(None)
        for item in self.alfred.focus_options:
            item.set_callback(callback=lambda _, length=item.length: self.enable(length)) if item is not None else None


    def on_tick(self, sender):
        sender.count += 1
        time_left = sender.end - sender.count
        mins, secs = divmod(time_left, 60)
        
        self.alfred.time_left.title = f'Time Left: {"< 1" if (mins <= 0) & (secs >=0) else mins} min'

        if sender.count == sender.end:
            self.disable()


class PomodoroMode(Mode):
    def __init__(self, timer: FocusTimer, alfred: Alfred):
        super().__init__(timer)
        self.alfred = alfred
        self.timer.set_callback(self.on_tick)
        self.sessions_left = 0
        self.sessions_length = 0
        self.break_length = 0
        self.is_break_time = False


    def init_pomodoro(self, _):
        # Set Pomodoro
        pom_vals = {
            'pom_length': {
                'message': 'How long would you like your sessions to be? (in minutes)',
                'title': 'Sessions Length',
                'default_text': '25',
                'val': 0
            },
            'pom_sessions': {
                'message': 'How many sessions would you like to do? (in minutes)',
                'title': 'Set Sessions',
                'default_text': '5',
                'val': 0
            },
            'pom_break': {
                'message': 'How long would you like your break to be? (in minutes)',
                'title': 'Set Break',
                'default_text': '10',
                'val': 0
            }
        }

        for pom in pom_vals:
            while pom_vals[pom]['val'] <= 0:
                pom_vals[pom]['val'] = int(rumps.Window(
                    message=pom_vals[pom]['message'], 
                    title=pom_vals[pom]['title'], 
                    default_text=pom_vals[pom]['default_text'], 
                    dimensions=(50,20), 
                    ok='Set', 
                    cancel='Cancel').run().text)
                
        self.sessions_left = pom_vals['pom_sessions']['val']
        self.sessions_length = pom_vals['pom_length']['val']
        self.break_length = pom_vals['pom_break']['val']
        self.enable()


    def enable(self):
        self.enable_focus(self.sessions_length)
        self.alfred.time_left.hidden = False
        self.alfred.sessions_left.title = f'Sessions Left: {self.sessions_left}'
        self.alfred.sessions_left.hidden = False
        self.alfred.pomodoro_end.set_callback(self.disable)


    def disable(self, sender=None):
        self.disable_focus()
        self.alfred.time_left.hidden = True
        self.alfred.sessions_left.hidden = True
        self.alfred.pomodoro_end.set_callback(None)


    def on_tick(self, sender):
        sender.count += 1
        time_left = sender.end - sender.count
        mins, secs = divmod(time_left, 60)

        self.alfred.time_left.title = f'{"Break" if self.is_break_time else "Focus"} Time Left: {"< 1" if (mins <= 0) & (secs >=0) else mins} min'

        if sender.count == sender.end:
            if not self.is_break_time:
                self.sessions_left -= 1
            
            if (self.is_break_time) & (self.sessions_left > 0):
                self.alfred.sessions_left.title = f'Sessions Left: {self.sessions_left}'
                self.is_break_time = False
                if self.sessions_left > 0:
                    sender.count = 0
                    self.enable()
            elif self.sessions_left > 0:
                self.is_break_time = True
                self.alfred.sessions_left.title = f'Sessions Left: {self.sessions_left}'
                self.disable()
                self.alfred.time_left.hidden = False
                self.alfred.sessions_left.hidden = False
            else:
                self.disable()
        


if __name__ == "__main__":
    Alfred().run()
