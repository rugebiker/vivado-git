# Vivado-git scripts
This scripts help to commit Vivado projects into Git.

### Dependencies
- Python 2.7
- OS: Tested on GNU/Linux and Windows
- Python and Vivado binaries must be in your PATH
  - To add Vivado to your path in Linux you can source "<Xilinx installation directory>/Vivado/<version>/settings64.sh". For Windows execute from the same directory "settings64.bat".
- Tested with Vivado 2017.2, 2017.3

### Folder structure
The project must have a specific folder structure. It is as follows:

```
.
+-- vivado-git # Directory containing the vivado-git scripts
|   +-- checkin.py # script to check in the project
|   +-- checkout.py # script to check out the project
|   +-- README.md # this readme file
|   +-- gitignore # .gitignore template to only commit sources and tcls
+-- workspace # Directory containing the Vivado project.
|   +-- <vivado_project> # Name must be the same as the Vivado project name
+-- sources # Directory containing all the sources (HDL files, constrains, etc.). The structure under this directory can be any
+-- ips # Directory containing all the packaged IPs. This is the top-level directory to be imported into the Vivado repositories
+-- tcl # Directory that will contain the generated tcl scripts to regenerate the project
|   +-- <vivado_project>.tcl # script to regenerate the project
|   +-- <vivado_project>.bd # directory containing the tcls to regenerate the block designs
```

**IMPORTANT**: It is very important that all the external IPs are cloned/copied into the project in the IPs folder. If one of them is missing, the project will fail to be regenerated. You can also add them as submodules.

### Setting up a Vivado project

1. Create the root folder and initialize it with git
2. Add this project as a submodule:
```
git submodule add git@axgit03.axon.nl:Tools/vivado-git.git
```
3. Create the following directories in the root folder: **workspace**, **sources**. Optionally create an **ips** if IPs versioned separately are to be included in the project
   - All sources (HDL files, constrain files, etc.) should be in the *sources* folder, and all external IPs that won't be committed with the project should be in *ips* directory. For SDK support scroll down
4. Create your Vivado project under **workspace**, so that you would have a similar structure: workspace -> vivado_project -> vivado_project.xpr
5. Optionally copy gitignore to the root folder .gitignore

### Scripts usage

#### Commiting a project
1. Run the python script **checkin.py** and it will automatically create the *tcl* directory with the related tcl scripts
2. Commit only the **sources** and **tcl** folders

### Regenerating a project
To regenerate a project it must have been checked-in with these scripts. To regenerate a project:

1. If your project depends on external IPs, make sure to clone/include them in the IPs directory before running the script, otherwise the project **won't** be generated
2. Run the python script **checkout.py** and it will automatically regenerate the project into the **workspace** directory (be sure to not have a previous generated project already)

### Xilinx SDK support
Xilinx SDK is not yet included in these scripts. A way to also include the SDK projects without much work is as follows:

- Setting up the SDK project the first time
  1. Export the *Hardware Definition Files* (HDF) from Vivado into a separate directory (eg. SDK) in the root folder
  2. Open the Xilinx SDK from Vivado using the same folder as workspace. The Xilinx SDK should automatically recognize the *HDF* file and create a project for it
  3. Create new applications as desired

- Commit the SDK projects
  1. Clean the projects. Make sure that they don't get built again after being cleaned. This is to avoid committing binaries and unnecessary files
  2. Make sure to only include for the commit the projects you want and ignore everything else. The HDF file and the project around it can be discarded as they can be automatically regenerated

- Regenerate the SDK projects
  1. Regenerate the Vivado project as described above
  2. From Vivado, export the HDF file into the same directory containing the committed projects
  3. Open the Xilinx SDK from Vivado defining that same directory as the workspace

### Important note
Always check the logs to see that there was no error checking in or out the project!!!
