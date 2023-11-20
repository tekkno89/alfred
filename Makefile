ALFRED_HOME=${HOME}/.alfred
install: SHELL:=/bin/bash
install:
   @pip install -r requirements.txt
   @mkdir -p ${ALFRED_HOME}
   @cp -n focus.py ${ALFRED_HOME}/focus
   @chmod 744 ${ALFRED_HOME}/focus
   @cp -n ./assets/macos-focus-mode.shortcut ${ALFRED_HOME}
   @echo ""
   @echo "Click 'Add Shortcut' when the window appears"
   @sleep 4
   @open ${ALFRED_HOME}/macos-focus-mode.shortcut
   @echo "Setup complete"
   @echo "Add ${ALFRED_HOME} to your PATH"