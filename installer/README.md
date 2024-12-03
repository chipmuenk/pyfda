# Installing PyFDA
To install PyFDA using the install script, simply make the file "install.sh" executable and execute it:

```
$> chmod +x ./install.sh
$> ./install.sh
```

The script will install PyFDA to the directory specified by the $INSTALL_DIR variable, which defaults to $HOME/.pyfda.

It will also create a .desktop file in the location specified by $DESKTOP_FILE.

If you wish to change these paths, simply edit the variables in the script.

# Removing PyFDA
You can remove PyFDA by symply running the file "uninstall.sh".

MAKE SURE THAT THE DIRECTORY SPECIFIED IN THE SCRIPT IS CORRECT!

```
$> chmod +x ./uninstall.sh
$> ./uninstall.sh
```

The script will delete the directory specified by the $INSTALL_DIR variable, which defaults to $HOME/.pyfda.
