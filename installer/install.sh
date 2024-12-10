#!/bin/bash
INSTALL_DIR=$HOME/.pyfda
DESKTOP_FILE=$HOME/.local/share/applications/pyfda.desktop

# Check if python3 is installed
if ! command -v python3 > /dev/null ; then
		echo "Error: Python 3 is not in PATH!";
		exit 1;
fi
echo "This script will create a desktop starter for pyfda under"
echo "$DESKTOP_FILE"
echo
read -p "Do you want to do this [y/N] ?" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
	# # Create install directory, exit on fail
	# if [ ! -d "$INSTALL_DIR" ]; then
	# 	mkdir $INSTALL_DIR || exit 1;
	# fi

#	python3 -m venv $INSTALL_DIR/venv
#	source $INSTALL_DIR/venv/bin/activate
#	python3 -m pip install pyfda
#	deactivate

	# Create Desktop file
	cp ./icon.png $INSTALL_DIR
	echo "[Desktop Entry]" > $INSTALL_DIR/pyfda.desktop
	echo "Name=PyFDA" >> $INSTALL_DIR/pyfda.desktop
	echo "Comment=PyFDA Filter Design Tool" >> $INSTALL_DIR/pyfda.desktop
	echo "Exec=/bin/bash -c 'source $INSTALL_DIR/venv/bin/activate && $INSTALL_DIR/venv/bin/python $INSTALL_DIR/venv/bin/pyfdax'" >> $INSTALL_DIR/pyfda.desktop
	echo "Icon=$INSTALL_DIR/icon.png" >> $INSTALL_DIR/pyfda.desktop
	echo "Terminal=false" >> $INSTALL_DIR/pyfda.desktop
	echo "Type=Application" >> $INSTALL_DIR/pyfda.desktop

	ln $INSTALL_DIR/pyfda.desktop $DESKTOP_FILE
else
	echo "Aborted."
fi