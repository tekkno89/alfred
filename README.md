# Alfred
Alfred is a personal assistant to help with daily work. This project is still a work in progress. The only current feature is `focus` and is provided as a CLI tool. This will eventually be rolled into an app that runs in the background with other features, for example, updating your communications apps such as Slack with a DND status.

### Focus
The `focus` feature provides a way for you to enable the Mac Do Not Disturb mode. Currently DND only allows you to specify a DND of 1 hour or until the next morning. `focus` allows you to provide a more granular time limit of as many minutes you would like. Not only does it enable DND, it will also hide your App Dock to help you focus on your work and not be distracted by any email or slack notifications that occur during your focus time. A bonus that is built in to DND is that it will sync across your other Mac devices, like your iPhone and iPad.

## Usage
Once the focus script is [installed](#installation), you just need to call the `focus` command from your terminal.
### Enable Focus
To enable you just need to need to use the `-e` flag followed by how many minutes you would like to focus. After focus has reached the amount of time you have set, it will disable DND and unhide your App Dock. The following is an example of enabling focus for 30 minutes:
```
focus -e 30
```
### End Focus Early
If you would like to end your focus mode early, you can call the `focus` command again with the `-d` flag and it will end DND and unhide your App Dock.
```
focus -d
```

## Installation
`focus` works by using a custom Mac Shortcuts. The makefile will help you install that Shortcut and setup the rest of the app for you. After running the Makefile you will just need to add the focus app to your PATH. See the [Set focus Path](#set-focus-path) section if you need help with that. Run the following command to install `focus`, NOTE - you will be prompted with a window at one point to install the shortcut, you will just need to click the `Add Shortcut` button.
```
make install
```

### Set focus Path
If you use Bash shell you can run the following command in your terminal:
```
echo $PATH=$PATH:~/.alfred >> ~/.bashrc
```
For zshell, use the following:
echo $PATH=$PATH:~/.alfred >> ~/.zshrc