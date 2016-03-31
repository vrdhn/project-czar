#!/usr/bin/env python3


import os
import os.path
import sys

import pathlib




def tell(*args):
    print("echo",
          *["'%s'"%x for x in args],';')


def get_prjdir():
    """ Traverse up to fine the project-czar.txt"""    
    at = pathlib.Path.cwd()
    fn = 'project-czar.txt'
    while at.name != '' :
        if (at/fn).is_file():
            return at.as_posix()
        at = at.parent
    return None


def get_dirs():
    curdir = get_prjdir()
    linkf = pathlib.Path.home()/'.project-czar'
    curprj = os.readlink(linkf.as_posix()) if linkf.is_symlink() else None
    return (curdir, curprj, linkf)
    
def verify_projectdir( update = False):
    """ verify that current dir is current project.
    update=True updates if not already set """
    ( curdir, curprj, linkf ) = get_dirs()
    if not curdir:
        tell("Not in a project directory. To mark a dir-tree:")
        tell("touch project-czar.txt")
        sys.exit(1)

        
    if update:
        if curprj == None:
            linkf.symlink_to(curdir,True)
            return
        elif curprj == curdir:
            tell("Project already started :", curprj)
            sys.exit(1)
        else:
            tell("You need to stop current project first: ", curprj)
            sys.exit(1)
    else:
        if curprj == None:
            tell("Project ", curdir," not started")
            sys.exit(1)
        elif curprj == curdir:
            return
        else:
            tell("You are not in project directory: ", curprj, curdir)
            sys.exit(1)
        

def cmd_info():
    ( curdir, curprj, linkf ) = get_dirs()
    tell(" Project Directory :", curdir)
    tell(" Running Project   :", curprj)


def cmd_help():
    tell(". Project - Czar Usage:")
    tell(".     i -- info ")
    tell(".     +,start -- start clock")
    tell(".     -,stop -- stop clock")
    tell(".     t,task -- add a task to do")
    tell(".     l,list -- list tasks")
    tell(".     d,done -- mark # task done")
    tell(".     n,note -- edit notes of active task")


        
    
def cmd_start(txt):
    verify_projectdir(True)
    addlog('start',txt)

def cmd_stop(txt):
    verify_projectdir()
    addlog('stop',txt)
    linkf = pathlib.Path.home()/'.project-czar'
    linkf.unlink()
    

def addlog(cmd,notes):
    tell("Loggin ", cmd, *notes)
###

if len(sys.argv) < 2 :
    cmd_info()
elif sys.argv[1] in ( 'i', 'info' ) :
    cmd_info()
elif sys.argv[1] in ( '+', 'start' ) :
    cmd_start(sys.argv[2:])
elif sys.argv[1] in ( '-', 'stop' ) :
    cmd_stop(sys.argv[2:])
else:
    cmd_help()


    





