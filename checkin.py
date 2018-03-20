import sys
from subprocess import call, Popen, PIPE, STDOUT
import glob, os
import ntpath
import re
from sys import platform
from shutil import copytree, rmtree, copy

# Change to the correct directory
if not os.path.exists("vivado-git/checkin.py"):
    BasePath = os.path.dirname(os.path.realpath(__file__))
    BasePath = os.path.dirname(os.path.realpath(BasePath))
    os.chdir(BasePath)

# If there are more than 2 projects, print error and exit
if sum(os.path.isdir(os.path.join('workspace', i)) for i in os.listdir('workspace')) > 1:
    print "Error: Found more than 2 projects in the workspace directory"
    sys.exit()

# Find the Vivado project
for VivadoProject in glob.glob("workspace/*/*.xpr"):
    print "Found Vivado project at: " + VivadoProject

ProjectName = ntpath.basename(ntpath.splitext(VivadoProject)[0])
SourcesBdDir = "tcl/" + ProjectName + ".bd"

if platform == "win32":
    VivadoProcess = Popen(["vivado", "-version"], shell=True, stdout=PIPE)
else:
    VivadoProcess = Popen(["vivado", "-version"], stdout=PIPE)
VivadoVersion = VivadoProcess.stdout.read()
VivadoRegEx = re.match(r"^Vivado (v.*) ", VivadoVersion)
VivadoInstalled = VivadoRegEx.group(1)
if VivadoInstalled in ("v2017.2", "v2017.3", "v2017.4"):
    print ("Vivado version being used: " + VivadoInstalled)
else:
    print ("Warning: Generating scripts with an untested Vivado version, please test the checkout script after generating the scripts")

# Create folders if they don't exist
if VivadoInstalled == "v2017.2":
    if not os.path.isdir(SourcesBdDir):
        os.makedirs(SourcesBdDir)

if not os.path.isdir("tcl"):
    os.makedirs("tcl")

print "Exporting Project TCL from Vivado"
# Open vivado depending on the OS
if platform == "win32":
    vp = Popen(["vivado", '-nojournal', '-nolog', '-mode', 'tcl', VivadoProject], shell=True, stdin=PIPE)
else:
    vp = Popen(["vivado", '-nojournal', '-nolog', '-mode', 'tcl', VivadoProject], stdin=PIPE)

# Give commands to vivado to export project tcl and block design tcls
if VivadoInstalled == "v2017.2":
    vp.communicate(input="write_project_tcl -force \".exported.tcl\"\n; foreach {bd_file} [get_files -filter {FILE_TYPE == \"Block Designs\"}] { open_bd_design $bd_file; write_bd_tcl \"" + SourcesBdDir + "/[file rootname [file tail $bd_file]].tcl\"; close_bd_design [file rootname [file tail $bd_file]]}\n"),[0]
else:
    vp.communicate(input="write_project_tcl -force \".exported.tcl\"\n"),[0]

rem = 0
total_sources = 0
bad_sources = 0
count_sources = 0
block_design = 0
XciFile = 0
fnormalize_wrapper = ""
fset_wrapper = ""
wrapper_description = 0
# The tcl is stored in a temporary file so it can be processed and the end result is saved in /tcl/ folder
with open(".exported.tcl", 'r') as fin:
    with open("tcl/" + ProjectName + ".tcl", 'w') as fout:
        print ("Lines removed from original tcl:\n")
        for line in fin:
            if rem == 0:
                # Count the sources
                if count_sources == 1:
                    if re.match(r"^]", line) == None:
                        total_sources = total_sources + 1
                    else:
                        # If the total sources is same as the removed ones, remove the line after as there are no sources to process
                        if total_sources == bad_sources:
                            rem = 1
                        count_sources = 0
                        bad_sources = 0
                        total_sources = 0
                
                # Save regex for XCI IPs
                XciRegEx = re.match(r"^\s+\"\[file normalize \"\$origin_dir/(workspace/[^ ]+/ip/([^ ]+))/([^ /]+.xci)\"]\"\\", line)

                # Save regex for the create_project command
                CreateProjectRegEx = re.match(r"^create_project.* -part (.*)", line)

                # Modify "create_project" command to store the project inside the workspace directory
                if CreateProjectRegEx != None:
                   fout.write("create_project " + ProjectName + " workspace/" + ProjectName + " -part " + CreateProjectRegEx.group(1)) 

                # Count the number of sources to import
                elif re.match(r"^set files \[list \\", line) != None:
                    count_sources = 1
                    fout.write(line)

                # Remove block design wrappers. They will be auto-generated later
                elif re.match(r"^set file \"hdl/[^ /]+_wrapper\.v(?:hd)?\"", line) != None:
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)
                    fset_wrapper = fset_wrapper + line
                    wrapper_description = 1
                    rem = 3
                    block_design = 1

                # Remove all the references to block design
                elif re.match(r"^\s+\"\[file normalize \"(.*)\.srcs/[^ /]+/bd/([^ /]+)/\2.bd\"]\"\\", line) != None:
                    bad_sources = bad_sources + 1
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)
                    block_design = 1

                # Remove all the references to prj files
                elif re.match(r"^\s+\"\[file normalize \".*/.*\.srcs/.*/*\.prj\"]\"\\", line) != None:
                    bad_sources = bad_sources + 1
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)

                # Remove the block design wrappers. They will be auto-generated later
                elif re.match(r"^\s+\"\[file normalize \"(.*)\.srcs/[^ /]+/bd/([^ /]+)/hdl/\2_wrapper.v(?:hd)?\"]\"\\", line) != None:
                    bad_sources = bad_sources + 1
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)
                    fnormalize_wrapper = fnormalize_wrapper + line
                    block_design = 1

                # Remove the block design wrappers. They will be auto-generated later
                elif re.match(r"^\s+\"\[file normalize \".*/.*\.srcs/[^ /]+/[^ ]+/hdl/.*_wrapper.v(?:hd)?\"]\"\\", line) != None:
                    correct_wrapper = re.match(r"(^\s+\"\[file normalize \".*/.*\.srcs/[^ /]+/)[^ ]+/hdl/((.*)_wrapper.v(?:hd)?)(\"]\"\\)", line)
                    correct_route = correct_wrapper.group(1) + "bd/" + correct_wrapper.group(3) + "/hdl/" + correct_wrapper.group(2) + correct_wrapper.group(4)
                    bad_sources = bad_sources + 1
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)
                    fnormalize_wrapper = fnormalize_wrapper + correct_route + "\n"
                    block_design = 1

                # Remove the block design wrappers. They will be auto-generated later
                elif re.match(r"^set file \"(.*)\.srcs/[^ /]+/bd/([^ /]+)/hdl/\2_wrapper.v(?:hd)?\"", line) != None:
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)
                    rem = 3
                    block_design = 1

                # Remove the pjr files.
                elif re.match(r"^set file \"[^ /]+/[^ /]+\.prj\"", line) != None:
                    print(line)
                    fout.write("## Vivado-git removed ## " + line)
                    rem = 3

                # Copy xci IPs to sources and link to them
                elif XciRegEx != None:
                    if not os.path.isdir("sources/ips"):
                        os.makedirs("sources/ips")
                    print(line)
                    if os.path.isdir("sources/ips/" + XciRegEx.group(2)):
                        rmtree("sources/ips/" + XciRegEx.group(2))
                    try:
                        copytree(XciRegEx.group(1), "sources/ips/" + XciRegEx.group(2))
                    except OSError:
                        copy(XciRegEx.group(1) + ".xcix", "sources/ips/")
                    fout.write(" \"[file normalize \"sources/ips/" + XciRegEx.group(2) + "/" + XciRegEx.group(3) + "\"]\"\\\n")
                    XciFile = 2

                # Write the lines to the new file
                else:
                    if XciFile > 0:
                        if XciFile == 2:
                            fout.write(line)
                        if XciFile == 1:
                            fout.write("add_files -norecurse -fileset $obj $files\n")
                        XciFile = XciFile - 1
                    else:
                        fout.write(line)

            # Necessary as the block design wrappers have also some extra lines belonging to them that need to be removed
            else:
                rem = rem - 1;
                if wrapper_description == 1:
                    fset_wrapper = fset_wrapper + line 
                    if rem == 0:
                        fset_wrapper = fset_wrapper + "\n"
                        wrapper_description = 0
                fout.write("## Vivado-git removed ## " + line)
                print(line)
    
        fout.write("\n")

        # At the end of the tcl, add commands to include the block designs (if available) and generate the wrappers
        if block_design == 1:
            if VivadoInstalled == "v2017.2":
                print("Adding block design tcls\n")
                for file in os.listdir(SourcesBdDir):
                    if file.endswith(".tcl"):
                        fout.write("source " + SourcesBdDir + "/" + file + "\n")

            #fout.write("add_files -norecurse -force [make_wrapper -files [get_files *.bd] -top]\n")
            fout.write("make_wrapper -files [get_files *.bd] -top\n")
            if fnormalize_wrapper != "":
                fout.write("set files [list \\\n")
                fout.write(fnormalize_wrapper)
                fout.write("]\n")
                fout.write("set imported_files [import_files -fileset sources_1 $files]\n")
                fout.write("\n")
                fout.write(fset_wrapper)

# Remove the temporary tcl file
os.remove(".exported.tcl")
