#!/usr/bin/python3
""" Python rsync backup script

Copyright 2013-2014 Sebastian Kraft

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# ------------------------------------------------------
# Module imports
import time
import subprocess
import os
import sys
import re
import configparser


# ------------------------------------------------------
# Some general functions

def ask_ok(prompt, retries=4, complaint='Please type yes or no...'):
    """Ask the user to confirm with yes or no."""
    while True:
        ok = input(prompt)
        if ok in ('y', 'Y', 'yes', 'Yes'):
            return True
        if ok in ('n', 'N', 'no', 'No'):
            return False
        print(complaint)


def print2log(s, filehandle=0):
    """Push string to STDOUT and optionally append it to an already open log file"""
    global WRITE_LOGFILE
    sys.stdout.buffer.write(bytes(s, "utf-8"))
    sys.stdout.flush()  
    # '\r' has no effect for file write
    if (WRITE_LOGFILE==True) and filehandle and (s.find('\r')==-1):
        filehandle.write(bytes(s, "utf-8"))


def find_last_backup(backupRoot):
    """Find subfolders of pattern 2013-06-24T18:44:31 and determine the most recent one by its name.
       The full path name of the most recent subfolder will be returned or None if no subfolder was found.
    """
    prevBackupsFound = False
    if os.path.exists(backupRoot):
        dirListing = os.listdir(backupRoot)
        dirListing = [name for name in os.listdir(backupRoot) if os.path.isdir(os.path.join(backupRoot, name))]
        # match directory names of type 2013-06-24T18:44:31
        rex = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}$')
        dirListing = [x for x in dirListing if rex.match(x)]
        numOldBackups = len(dirListing)
        if numOldBackups > 0:
            # dirListing.sort(key=lambda s: os.path.getmtime(os.path.join(current_backup_target, s)))
            dirListing.sort()
            dirListing.reverse()
            return os.path.join(backupRoot, dirListing[0])

    return None


# ------------------------------------------------------
# Main program

# ------------------------------------------------------
# open and parse the config file
config = configparser.ConfigParser()

if len(sys.argv) != 2:
    print("ERROR: No config file specified!\nUsage: pyrsyncback myconfig.ini")
    sys.exit()

if os.path.exists(sys.argv[1]):
    config.read(sys.argv[1])
else:
    print("ERROR: Config file not found!")
    sys.exit()

if len(config.sections()) < 2:
    print("ERROR: Empty or invalid config file!")
    sys.exit()

BACKUP_LIST = config.sections()
BACKUP_LIST.remove("General")
WRITE_LOGFILE = config.getboolean("General", "WriteLogfile")
TARGET_DIRECTORY = config.get("General", "TargetFolder")


# check if target directory is mounted
if not os.path.exists(TARGET_DIRECTORY):
    print("ERROR: Target directory \n>> "+TARGET_DIRECTORY+" <<\nis not available! If it is located on an external or network drive check if it is correctly mounted in the expected place.")
    sys.exit()

# prepare logfile
if WRITE_LOGFILE:
    logFile = open(os.path.join(TARGET_DIRECTORY, 'rsync_' + time.strftime( "%Y-%m-%dT%H:%M:%S") + '.log'), 'wb')
else:
    logFile = 0

# ------------------------------------------------------
# iterate over backup entries
for currBackupItem, key in enumerate(BACKUP_LIST):

    backupEntry = dict(config.items(key))
    backupEntry["path"] = key

    if ("group" not in backupEntry):
        print2log("Group is a mandatory entry in a backup section!\n", logFile)
        sys.exit()

    countStr = "("+str(currBackupItem)+"/"+str(len(BACKUP_LIST))+")"
    
    print2log("\n-----------------------------------------------------------\n", logFile)
    print2log("Backing up <" + backupEntry["path"] + "> " + countStr +"\n", logFile)
    print2log("-----------------------------------------------------------\n", logFile)

    # check if source directory exists    
    if not backupEntry["path"].startswith("ssh://") and not os.path.exists(backupEntry["path"]):
        print2log("ERROR: Source directory does not exist! Skipping...\n", logFile)
        input("Press any key to proceed with next backup item...")
        continue

    # build filename for target directory
    # Scheme: TARGET_DIRECTORY/GROUP/FolderName/TIMESTAMP/
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    backupFolderName = os.path.basename(os.path.normpath(backupEntry["path"]))
    groupRoot = os.path.join(TARGET_DIRECTORY, backupEntry["group"])
    backupRoot = os.path.join(TARGET_DIRECTORY, backupEntry["group"], backupFolderName)

    # check for previous backups
    previous_backup_link = ''
    last_backup = find_last_backup(backupRoot)

    if last_backup:
        print2log("+ Previous backup will be used as hard link reference: "+last_backup+"\n", logFile)
        previous_backup_link = '--link-dest="' + last_backup + '" '
    else:
        print2log("WARNING: No previous data for incremental backups were found!\n", logFile)
        if ask_ok("Should a complete backup be performed? (y/n)"):
            if not os.path.exists(groupRoot):
                os.mkdir(groupRoot)
            if not os.path.exists(backupRoot):
                os.mkdir(backupRoot)
        else:
            # continue with next backup item
            continue            
            
    # assemble rsync commandline
    backupDirResolved = backupEntry["path"].replace("ssh://", "-e ssh ", 1) + os.path.sep
    if "exclude" in backupEntry:
        excludeStr = ['--exclude=%s' % x.strip() for x in backupEntry["exclude"].split(',')]
    else:
        excludeStr = ""
    rsynccmd  = 'rsync -aP ' + previous_backup_link + ' ' + backupDirResolved + ' ' + os.path.join(backupRoot, timestamp + '_tmp') + ' ' + ' '.join(excludeStr)
    print2log("+ CMD>$ " + rsynccmd + "\n\n", logFile)

    # run the rsync process
    rsyncproc = subprocess.Popen(rsynccmd,
                                 shell=True,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 )

    # read rsync output and print to console and log file
    while True:
        next_line = rsyncproc.stdout.readline().decode("utf-8")
        if not next_line:
            break
        print2log("+" + countStr + "+ " + next_line, logFile)

    # wait until process is really terminated and check the exit code
    exitcode = rsyncproc.wait()
    if exitcode == 0:
        os.rename(os.path.join(backupRoot, timestamp+"_tmp"), os.path.join(backupRoot, timestamp))
        print2log("done \n\n", logFile)
    else:
        print2log("\nWARNING: looks like some error occurred :( \n\n", logFile)
        break

# ------------------------------------------------------
# final actions
if (WRITE_LOGFILE is True) and logFile:
    logFile.close()
