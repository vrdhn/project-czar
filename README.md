# project-czar

Command line project management for multiple people on multiple projects.


# data files

project-czar will maintain data files in ~/czar, and can be be overridden
by CZAR_HOME. This directory should be managed by version control.

The file project-current will have the uuid of current projet
The file project-list will have list of uuid to working directory mapping
The files project-{uuid}  will be the data file




# Usage

Define in your ~/.bashrc or equivalent:

    p ()
    {
        /usr/bin/python3 <abs path to>/project-czar/project-czar.py "$@"
    }

Then run 'p' for info, and 'p h' for help




	
	




