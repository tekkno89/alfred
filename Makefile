ALFRED_HOME=$HOME/.alfred
install:
	pip install -r requirements.txt
	mkdir $ALFRED_HOME
	cp focus.py $ALFRED_HOME/focus
	cp ./assets/macos-focus-mode.shortcut $ALFRED_HOME
	read "Click `Add Shortcut` when the window appears. Hit enter when ready"
	open $ALFRED_HOME/macos-focus-mode.shortcut
	echo "Setup complete"
	echo "Add ${ALFRED_HOME} to your PATH"