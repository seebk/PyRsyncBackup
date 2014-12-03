PyRsyncBackup
=============

__WARNING:__ PyRsyncBackup is currently not intended to be a ready 
to use backup software, just use it as a basis to create your own 
scripts and thoroughly test before using it for real backups!

PyRsyncBackup is a short Python script to perform backups using the 
rsync utility. The main design goal was simplicity and transparency. 
It basically just provides a front-end to configure backup directories 
and targets. Furthermore, it automatically references the most recent backup 
folder to serve as a hard link source which implements differential backups
in a very smart way.

Additional information about rsync and also about the hard-link backup  
strategy can be found here:

* [rsync man page](http://rsync.samba.org/documentation.html)
* [detailed rsync tutorial](http://www.mikerubel.org/computers/rsync_snapshots/)