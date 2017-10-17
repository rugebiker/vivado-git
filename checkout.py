import sys
from subprocess import call
import glob, os
from subprocess import Popen, PIPE, STDOUT
import re
from sys import platform

# Change to the correct directory
if not os.path.exists("vivado-git/checkin.py"):
    BasePath = os.path.dirname(os.path.realpath(__file__))
    BasePath = BasePath[:-10]
    os.chdir(BasePath)

# Look for the tcl script
for VivadoProject in glob.glob("tcl/*.tcl"):
    print "Found tcl script at: " + VivadoProject

# Create folder if it doesn't exist
if not os.path.isdir("workspace"):
    os.makedirs("workspace")

# Check the Vivado version from the generated tcl.
VivadoTcl = ""
with open(VivadoProject, 'r') as fin:
    for line in fin:
        RegEx = re.match(r"^# Vivado \(TM\) (v.*) ", line)
        if RegEx != None:
            VivadoTcl = RegEx.group(1)
            break

# Check the installed Vivado version. Correct params depending on the OS
if platform == "win32":
    VivadoProcess = Popen(["vivado", "-version"], shell=True, stdout=PIPE)
else:
    VivadoProcess = Popen(["vivado", "-version"], stdout=PIPE)
VivadoVersion = VivadoProcess.stdout.read()
VivadoRegEx = re.match(r"^Vivado (v.*) ", VivadoVersion)
VivadoInstalled = VivadoRegEx.group(1)

# Compare both versions, and if they are different then ask if it is fine to continue
if VivadoTcl == VivadoInstalled:
    print "Vivado version matches: " + VivadoTcl + "\n"
else:
    print "This project was built using Vivado " + VivadoTcl + " and your installed Vivado version is " + VivadoInstalled + "."
    answer = raw_input( "Would you still like to continue generating the project? (y,N):   ")
    if not (answer == 'y' or answer == 'Y'):
        sys.exit()

# Call vivado to run the tcl script. Correct params depending on the OS
if platform == "win32":
    call(["vivado", '-nojournal', '-nolog', '-mode', 'batch', '-source', VivadoProject], shell=True)
else:
    call(["vivado", '-nojournal', '-nolog', '-mode', 'batch', '-source', VivadoProject])
