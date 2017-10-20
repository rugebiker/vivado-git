import sys
from subprocess import call
import glob, os
import ntpath
from subprocess import Popen, PIPE, STDOUT
import re
from sys import platform

# Change to the correct directory
if not os.path.exists("vivado-git/checkin.py"):
    BasePath = os.path.dirname(os.path.realpath(__file__))
    BasePath = BasePath[:-10]
    os.chdir(BasePath)

# Find the Vivado project
for VivadoProject in glob.glob("workspace/*/*.xpr"):
    print "Found Vivado project at: " + VivadoProject

ProjectName = ntpath.basename(ntpath.splitext(VivadoProject)[0])
SourcesBdDir = "tcl/" + ProjectName + ".bd"

# Create folders if they don't exist
if not os.path.isdir("tcl"):
    os.makedirs("tcl")

if not os.path.isdir(SourcesBdDir):
    os.makedirs(SourcesBdDir)

print "Exporting Project TCL from Vivado"
# Open vivado depending on the OS
if platform == "win32":
    vp = Popen(["vivado", '-nojournal', '-nolog', '-mode', 'tcl', VivadoProject], shell=True, stdin=PIPE)
else:
    vp = Popen(["vivado", '-nojournal', '-nolog', '-mode', 'tcl', VivadoProject], stdin=PIPE)

# Give commands to vivado to export project tcl and block design tcls
vp.communicate(input="write_project_tcl -force \".exported.tcl\"\n; foreach {bd_file} [get_files -filter {FILE_TYPE == \"Block Designs\"}] { open_bd_design $bd_file; write_bd_tcl \"" + SourcesBdDir + "/[file rootname [file tail $bd_file]].tcl\"; close_bd_design [file rootname [file tail $bd_file]]}\n"),[0]

rem = 0
total_sources = 0
bad_sources = 0
count_sources = 0
# The tcl is stored in a temporary file so it can be processed and the end result is saved in /tcl/ folder
with open(".exported.tcl", 'r') as fin:
    with open("tcl/" + ProjectName + ".tcl", 'w') as fout:
        print ("Lines removed from original tcl:\n")
        for line in fin:
            if rem == 0:
                
                if count_sources == 1:      # Count the sources
                    if re.match(r"^]", line) == None:
                        total_sources = total_sources + 1
                    else:
                        if total_sources == bad_sources:    # If the total sources is same as the removed ones, remove the line after as there are no sources to process
                            rem = 1
                        count_sources = 0

                CreateProjectRegEx = re.match(r"^create_project.* -part (.*)", line)

                if CreateProjectRegEx != None:      # Modify "create_project" command to store the project inside the workspace directory
                   fout.write("create_project " + ProjectName + " workspace/" + ProjectName + " -part " + CreateProjectRegEx.group(1)) 

                elif re.match(r"^set files \[list \\", line) != None:   # Count the number of sources to import
                    count_sources = 1
                    fout.write(line)

                elif re.match(r"^\s+\"\[file normalize \"(.*)\.srcs/[^ /]+/bd/([^ /]+)/\2.bd\"]\"\\", line) != None:    # Remove all the references to block design
                    bad_sources = bad_sources + 1
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)

                elif re.match(r"^\s+\"\[file normalize \"(.*)\.srcs/[^ /]+/bd/([^ /]+)/hdl/\2_wrapper.v(?:hd)?\"]\"\\", line) != None:  # Remove the block design wrappers. They will be auto-generated later
                    bad_sources = bad_sources + 1
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)

                elif re.match(r"^set file \"(.*)\.srcs/[^ /]+/bd/([^ /]+)/hdl/\2_wrapper.v(?:hd)?\"", line) != None:    # Remove the block design wrappers. They will be auto-generated later
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)
                    rem = 3

                else:   # Write the lines to the new file
                    fout.write(line)

            else:   # Necessary as the block design wrappers have also some extra lines belonging to them that need to be removed
                rem = rem - 1;
                fout.write("## Vivado-git removed ## " + line)
                print(line)
    
        fout.write("\n")

        print("Adding block design tcls\n")

        # At the end of the tcl, add commands to include the block designs and generate the wrappers
        for file in os.listdir(SourcesBdDir):
            if file.endswith(".tcl"):
                fout.write("source " + SourcesBdDir + "/" + file + "\n")
                fout.write("add_files -norecurse -force [make_wrapper -files [get_files " + file.strip(".tcl") + ".bd] -top]\n")

# Remove the temporary tcl file
os.remove(".exported.tcl")
