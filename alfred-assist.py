import os
import rumps
import subprocess
from enum import Enum


class FocusState(Enum):
    ON = 1
    OFF = 2


class FocusManager:
    def __init__(self):
        pass

    def enable_focus(self, session_length):
        """Set Focus for X minutes"""
        self.set_dnd(FocusState.ON, session_length)
        self.toggle_dock()

    def disable_focus(self):
        self.set_dnd(FocusState.OFF, 0)
        self.toggle_dock()

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


class SessionTimer(rumps.Timer):
    def __init__(self, callback, interval):
        super().__init__(callback, interval)
        self.count = 0
        self.end = 0

    def reset(self):
        self.count = 0
        self.end = 0

    def start(self):
        self.reset()
        super().start()

    def stop(self):
        super().stop()
        self.reset()

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
            self.setup_timers()
            self.setup_menu()
    

    def setup_timers(self):
        self.focus_timer = SessionTimer(None, 1)
        self.pomodoro_timer = SessionTimer(None, 1)


    def setup_menu(self):
        self.focus_lengths = [1, 5, 10, 15, None, 20, 25, 30, 35, None, 40, 45, 50, 55, None, 60, 90]
        self.focus_options = []
        self.time_left = rumps.MenuItem('Time Left: 0:00')
        self.sessions_left = rumps.MenuItem('Sessions Left: 0')
        self.time_left.hidden = True
        self.sessions_left.hidden = True
        
        self.FocusMode = FocusMode(self.focus_timer, self)
        self.PomodoroMode = PomodoroMode(self.pomodoro_timer, self)

        for length in self.focus_lengths:
            if length:
                new_item = rumps.MenuItem(f'{length} min', callback=None)
                new_item.length = length
                new_item.set_callback(lambda _, length=new_item.length: self.FocusMode.start_focus(length))
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


class FocusMode:
    def __init__(self, timer: SessionTimer, alfred: Alfred):
        self.timer = timer
        self.alfred = alfred
        self.focus_manager = FocusManager()
        self.timer.callback = self.on_tick

    def start_focus(self, length):
        self.focus_manager.enable_focus(length)
        self.alfred.time_left.hidden = False
        self.alfred.end_focus.set_callback(self.end_focus)
        for item in self.alfred.focus_options:
            item.set_callback(None) if item is not None else None

    def end_focus(self, sender=None):
        self.timer.stop()
        self.focus_manager.disable_focus()
        self.alfred.time_left.hidden = True
        self.alfred.end_focus.set_callback(None)
        for item in self.alfred.focus_options:
            item.set_callback(callback=lambda _, length=item.length: self.start_focus(length)) if item is not None else None

    def on_tick(self, sender):
        sender.count += 1
        time_left = sender.end - sender.count
        mins, secs = divmod(time_left, 60)
        
        self.alfred.time_left.title = f'Time Left: {"< 1" if (mins <= 0) & (secs >=0) else mins} min'

        if sender.count == sender.end:
            self.end_focus()


class PomodoroMode:
    def __init__(self, timer: SessionTimer, alfred: Alfred):
        self.timer = timer
        self.alfred = alfred
        self.focus_manager = FocusManager()
        self.timer.callback = self.on_tick
        self.sessions_completed = 0
        self.sessions_length = 0
        self.break_length = 0
        self.is_break_time = False

    def init_pomodoro(self, _):
        # Set Pomodoro
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
                
        self.sessions_left = pom_vals['pom_sessions']['val']
        self.sessions_length = pom_vals['pom_length']['val']
        self.break_length = pom_vals['pom_break']['val']
        self.enable()

    def enable(self):
        if not self.is_break_time:
            self.focus_manager.enable_focus(self.sessions_length)
        else:
            self.focus_manager.disable_focus()
        
        self.alfred.time_left.hidden = False
        self.alfred.sessions_left.title = f'Sessions Left: {self.sessions_left - self.sessions_completed}'
        self.alfred.sessions_left.hidden = False
        self.alfred.pomodoro_end.set_callback(self.end_focus)
        self.alfred.pomodoro_start.set_callback(None)

        session_duration = self.sessions_length if not self.is_break_time else self.break_length
        self.timer.end = session_duration * 60
        self.timer.start()

    def end_focus(self, sender=None):
        self.timer.stop()
        self.focus_manager.disable_focus()
        self.alfred.time_left.hidden = True
        self.alfred.sessions_left.hidden = True
        self.alfred.pomodoro_end.set_callback(None)
        self.alfred.pomodoro_start.set_callback(self.init_pomodoro)

    def on_tick(self, sender):
        sender.count += 1
        time_left = sender.end - sender.count
        mins, secs = divmod(time_left, 60)

        mode_label = "Break" if self.is_break_time else "Focus"
        self.alfred.time_left.title = f'{mode_label} Time Left: {"< 1" if (mins <= 0) & (secs >=0) else mins} min'

        if sender.count == sender.end:
            if self.is_break_time:
                self.sessions_completed += 1
                if self.sessions_completed >= self.sessions_left:
                    self.end_focus()
                else:
                    self.is_break_time = False
                    self.enable()
            else:
                self.is_break_time = True
                self.enable()

if __name__ == "__main__":
    shortcut_name = 'alfred-focus-mode'  # Define your shortcut name here
    Alfred().run()