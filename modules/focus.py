import plistlib
import os
import sys
import subprocess
import click
import threading
import time
from datetime import datetime
from pprint import pprint


home_dir = os.getenv('HOME')
notify_config = home_dir + '/Library/Preferences/com.apple.ncprefs.plist'
dock_config = home_dir + '/Library/Preferences/com.apple.dock.plist'


def get_plist_file(plist_file):
    with open(plist_file, 'rb') as file:
        settings_file = plistlib.load(file)

    return settings_file


def check_dnd_stat(settings):
    dnd_val = plistlib.loads(settings['dnd_prefs'])

    return 'userPref' in dnd_val


def set_dnd(status):
    settings = get_plist_file(notify_config)
    dnd_stat = check_dnd_stat(settings)
    deserial_dnd = plistlib.loads(settings['dnd_prefs'])

    if (status == 'on') & (dnd_stat is True):
        print('DND is already enabled')
    elif (status == 'off') & (dnd_stat is False):
        print('DND is already disabled')
    elif status == 'on':
        user_pref_val = {'enabled': True, 'date': datetime.now(), 'reason': 1}
        deserial_dnd['userPref'] = user_pref_val
    elif status == 'off':
        deserial_dnd.pop('userPref')
    else:
        sys.exit('Status not recognized')

    updated_dnd = plistlib.dumps(deserial_dnd, fmt=plistlib.FMT_BINARY)
    subprocess.run(['/usr/bin/defaults', 'write', 'com.apple.ncprefs.plist', 'dnd_prefs', '-data', updated_dnd.hex()])
    subprocess.run(['/usr/bin/killall', 'usernoted'])


def hide_dock(state):
    if state == 'on':
        subprocess.run(['/usr/bin/defaults', 'write', 'com.apple.dock.plist', 'autohide', '-bool', 'TRUE'])
    elif state == 'off':
        subprocess.run(['/usr/bin/defaults', 'write', 'com.apple.dock.plist', 'autohide', '-bool', 'FALSE'])
    else:
        sys.exit('Status not recognized')

    subprocess.run(['/usr/bin/killall', 'Dock'])

def enable_focus():
    set_dnd('on')
    hide_dock('on')

def disable_focus():
    set_dnd('off')
    hide_dock('off')

def focus_daemon(min):
    time.sleep(min)
    disable_focus()

@click.command()
@click.argument('length')
def focus_command(length):
    """Set Focus for X minutes"""
    enable_focus()
    min = int(length) * 60
    pid = os.fork()

    if pid == 0:
        focus_daemon(min)
    elif pid > 0:
        click.echo(f'Focus set for {str(length)} minute(s)')


if __name__ == '__main__':
    focus_command()