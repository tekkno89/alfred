#!/usr/bin/env python3
from __future__ import annotations  # Enables automatic forward references
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
        self.app.disable_focus_menu()
        self.app.disable_pomodoro()
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
        self.app.enable_focus_menu()
        self.app.enable_pomodoro()
        

    def run_focus(self, sender):
        self.remaining_time -= 1
        mins, secs = divmod(self.remaining_time, 60)

        if self.remaining_time <= 0:
            self.stop()

        if (mins <= 0) & (secs >= 0):
            self.time_left_msg.title = f'Time Left: < 1 min'
        else:
            self.time_left_msg.title = f'Time Left: {mins} min'


class PomodoroTimer:
    def __init__(self, app: Alfred):
        self.work_duration = 0
        self.break_duration = 0
        self.total_sessions = 0
        self.is_work_period = True
        self.current_session = 0
        self.remaining_time = 0
        self.is_running = False
        self.timer = None
        self.app = app
        self.end_pomodoro = rumps.MenuItem('End Pomodoro', callback=self.stop)
        self.time_left_msg = rumps.MenuItem('Time Left')
        self.session_mode_msg = rumps.MenuItem('Session Mode')
        self.session_count_msg = rumps.MenuItem('Sessions')
        self.pomodoro_menu_items = [
            self.end_pomodoro.title,
            self.time_left_msg.title,
            self.session_mode_msg.title,
            self.session_count_msg.title
        ]


    def pomodoro_init(self):
        pom_vals = {
            'pom_length': {
                'message': 'How long would you like your sessions to be? (in minutes)',
                'title': 'Session Length',
                'default_text': '25',
                'val': 0
            },
            'pom_sessions': {
                'message': 'How many sessions would you like to do?',
                'title': 'Number of Sessions',
                'default_text': '5',
                'val': 0
            },
            'pom_break': {
                'message': 'How long would you like your break to be? (in minutes)',
                'title': 'Break Length',
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
                
        self.total_sessions = pom_vals['pom_sessions']['val']
        self.work_duration = pom_vals['pom_length']['val'] * 60
        self.break_duration = pom_vals['pom_break']['val'] * 60
        self.remaining_time = pom_vals['pom_length']['val'] * 60 


    def start(self, sender=None):
        self.pomodoro_init()
        if self.is_running:
            return
        self.is_running = True
        self.timer = rumps.Timer(self.run_pomodoro, 1)
        self.timer.start()
        self.app.disable_focus_menu()
        enable_focus(self.work_duration)

        self.app.menu.insert_after('Start Pomodoro', self.end_pomodoro)
        self.app.menu.insert_after('End Pomodoro', self.session_mode_msg)
        self.app.menu.insert_after('Session Mode', self.time_left_msg)
        self.app.menu.insert_after('Time Left', self.session_count_msg)
        self.session_count_msg.title = f'Sessions Complete: {self.current_session}/{self.total_sessions}'
        self.session_mode_msg.title = f'Mode: Focus'

        self.app.disable_pomodoro()
        print("Pomodoro Mode started!")


    def stop(self, sender=None):
        if self.timer:
            self.timer.stop()
        self.is_running = False
        self.app.enable_focus_menu()
        
        for item in self.pomodoro_menu_items:
            del self.app.menu[item]

        self.app.enable_pomodoro()
        disable_focus()
        print("Pomodoro Mode ended!")


    def run_pomodoro(self, sender):
        self.remaining_time -= 1
        mins, secs = divmod(self.remaining_time, 60)
        self.time_left_msg.title = f'Time Left: {mins}:{secs}'

        if self.remaining_time <= 0:
            # Check if session is complete
            if self.is_work_period:
                self.current_session += 1
                self.session_count_msg.title = f'Sessions Complete: {self.current_session}/{self.total_sessions}'
                if self.current_session >= self.total_sessions:
                    self.stop()
                    rumps.notification("Pomodoro Complete", "All sessions are done!", "", icon='assets/alfred-assist.icns')
                    return
                
            self.is_work_period = not self.is_work_period
            self.remaining_time = self.work_duration if self.is_work_period else self.break_duration
            
            if self.is_work_period:
                enable_focus(self.work_duration)
                self.session_mode_msg.title = 'Mode: Focus'
            else:
                disable_focus()
                self.session_mode_msg.title = 'Mode: Break'



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
        self.pomodoro_mode = rumps.MenuItem('Start Pomodoro', callback=PomodoroTimer(self).start)

        self.menu = [
            {'Focus': self.focus_submenu},
            self.pomodoro_mode
        ]


    def disable_focus_menu(self):
        """Disable focus menu items while a focus session is running."""
        for item in self.focus_options:
            if isinstance(item, rumps.MenuItem):
                item.set_callback(None)


    def enable_focus_menu(self):
        """Re-enable focus menu items when the session ends."""
        for item in self.focus_options:
            if isinstance(item, rumps.MenuItem):
                length = int(item.title.split()[0])
                item.set_callback(lambda _, length=length: FocusTimer(self).start(length * 60))  # `state=False` makes it clickable again


    def disable_pomodoro(self):
        self.pomodoro_mode.set_callback(None)


    def enable_pomodoro(self):
        self.pomodoro_mode.set_callback(callback=PomodoroTimer(self).start)
            
        
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
