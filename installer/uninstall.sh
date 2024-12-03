#!/bin/bash
INSTALL_DIR=$HOME/.pyfda
DESKTOP_FILE=$HOME/.local/share/applications/pyfda.desktop

echo "This script will uninstall pyfda and all files that belong to it."
echo "The following files and directories will be deleted:"
echo "$INSTALL_DIR"
echo "$DESKTOP_FILE"

echo
read -p "Are you sure you want to do this? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
		rm -r $INSTALL_DIR
		rm $DESKTOP_FILE
else
	echo "Aborted."
fi
