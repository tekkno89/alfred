# Alfred Assist
Alfred is a personal assistant to help with daily work. This project is still a work in progress, the only current feature is `Focus`. More features are coming soon, for example, updating your communications apps such as Slack with a DND status. If you have an idea for a feature, open an issue with the request.

### Focus
The `Focus` feature provides a way for you to enable the Mac Do Not Disturb mode. Currently DND only allows you to specify a DND of 1 hour, until the next morning, or indefinitely. `Focus` allows you to provide a more granular time limit of as many minutes you would like. Not only does it enable DND, it will also hide your App Dock to help you focus on your work and not be distracted by any email or slack notifications that occur during your focus time. A bonus that is built in to DND is that it will sync across your other Mac devices, like your iPhone and iPad. Also, wanted to give [arodik](https://github.com/arodik) thanks for the inpiration. This had to be refactored when Ventura rolled out.

## Installation

### Focus Setup
`Focus` works by using a custom Mac Shortcuts, you will not be able to use Focus until you have installed the shortcut. Here are the steps for setup: 

**Activate Focus Shortcut:**

- Upon successful installation, an Alfred Assist icon will appear in your menu bar.
- Click on the Alfred Assist icon.
- In the menu, select "Install Focus Shortcut."

<p align="center">
  <img src="docs/alfred_focus_install.png">
</p>

**Shortcut Installation:**

- A window will appear, prompting you to install the shortcut.
- Click the "Add Shortcut" button to complete the installation.

<p align="center">
  <img src="docs/alfred_focus_shortcut_add.png" width="30%">
</p>

**Restart Alfred Assist:**

- Focus will be inactive until the shortcut is installed.
- Quit Alfred Assist and relaunch the app.

**Access Focus Options:**

- After relaunching, you can now find and use the Focus options within the app.

<p align="center">
  <img src="docs/alfred_focus_options.png">
</p>
