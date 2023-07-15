#!/usr/bin/env python3

import os
import sys
import subprocess
import click
import time
#from datetime import datetime

home_dir = os.getenv('HOME')
pid_file = '/tmp/alfred_focus.pid'
shortcut_name = 'macos-focus-mode'


# Make sure the short cut is installed, have to use this method for osx 13
def check_shortcut_installed():
    pass


def set_dnd(status, length=30):
    if status == 'on':
        shortcut_cmd = f'shortcuts run {shortcut_name} <<< "on {length}"'
    else:
        shortcut_cmd = f'shortcuts run {shortcut_name} <<< "off"'

    subprocess.run(shortcut_cmd, shell=True)


# Decided to use osascript because restarting dock will launch all the app windows you have minimized
def toggle_dock():
    subprocess.run(
        ['osascript', '-e', 'tell application "System Events" to set autohide of dock preferences to not (autohide of dock preferences)']
    )


def enable_focus(length):
    """Set Focus for X minutes"""
    set_dnd('on', length)
    toggle_dock()
    pid = os.fork()

    if pid == 0:
        focus_daemon(length)
    elif pid > 0:
        click.echo(f'Focus set for {length} minute(s)')
        track_focus_process(pid)


def disable_focus(terminate=False):
    # This is for terminating focus before time is up
    if terminate:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as file:
                pid = file.read()
            os.kill(int(pid), 9)
            os.remove(pid_file)
        else:
            sys.exit('Focus does not appear to be running')

    set_dnd('off')
    toggle_dock()


def focus_daemon(min):
    time.sleep(min * 60)
    disable_focus()


def track_focus_process(pid):
    with open(pid_file, 'w') as file:
        file.write(str(pid))


@click.command()
@click.option('-e', '--enable', type=int)
@click.option('-d', '--disable', is_flag=True)
def focus_command(enable, disable):
    if enable:
        mins = enable
        enable_focus(mins)
    elif disable:
        disable_focus(True)


if __name__ == '__main__':
    focus_command()