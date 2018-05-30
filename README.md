PyRsyncBackup
=============

PyRsyncBackup is a short Python script to perform backups using the 
`rsync` utility. The main design goal was simplicity and transparency. 
It basically just provides a front-end to configure backup directories 
and targets. Furthermore, it automatically references the most recent 
backup folder to serve as a hard link source which implements differential 
backups in a very smart way.

Additional information about rsync and also about the hard-link backup 
strategy can be found here:

* [rsync man page](http://rsync.samba.org/documentation.html)
* [detailed rsync tutorial](http://www.mikerubel.org/computers/rsync_snapshots/)

Instructions
------------

Below is an example config similar to the supplied `config.ini` file in the 
repository to demonstrate the capabilities.

    # Example config file

    # --------------------------------------------------------------------
    # General options and backup target folder location
    [General]
    # Required options
    WriteLogfile=true
    TargetFolder=/media/USER/ExtHDD

    # Optional comma separated list of strings which will be expanded to the rsync
    # option --exclude=...
    #Exclude=*.tiff,tmp/*
    # --------------------------------------------------------------------

    # --------------------------------------------------------------------
    # Backup entry for a local folder
    # The full path name is specified in the section header between the []
    [/home/USER/Pictures]
    # Optionally define a backup group folder or folder name
    #Group=Desktop
    #Name=Images

    # Comma separated list of strings which will be expanded to the rsync
    # option --exclude=...
    #Exclude=*.tiff,tmp/*
    # --------------------------------------------------------------------

    # --------------------------------------------------------------------
    # Backup entry for a remote folder accessible by SSH
    [ssh://xyz@myserver.com:/var/data]
    #Group=Server
    #Exclude=cache*,tmp*
    # --------------------------------------------------------------------


To perform a backup, simply run

    python pyrsyncbackup.py config.ini



