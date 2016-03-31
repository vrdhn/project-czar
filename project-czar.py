#!/usr/bin/env python3


import os
import os.path
import sys

import pathlib
import json

import datetime
import uuid



def tell(*args):
    print( *["%s"%x for x in args],';')


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
    tell(".     n,note -- add note to # task")


        
    
def cmd_start(txt):
    verify_projectdir(True)
    addlog('start',txt)

def cmd_stop(txt):
    verify_projectdir()
    addlog('stop',txt)
    linkf = pathlib.Path.home()/'.project-czar'
    linkf.unlink()

def cmd_task(txt):
    verify_projectdir()
    addlog('task',txt)

    
def cmd_list():
    verify_projectdir()
    (ts,note)  = get_open_tass()
    ts.reverse()
    idx = 1
    for t in ts:
        print(idx,' -- ', ' '.join(t["notes"]))
        if t["uuid"] in note:
            for n in note[t["uuid"]]:
                print("        ",' '.join(n["notes"]))
        idx = idx + 1
        
def cmd_done(idx,txt):
    verify_projectdir()
    (ts, note) = get_open_tass()
    ts.reverse()
    task_uuid = ts[idx-1]["uuid"]
    addlog('done',txt,{ 'task_uuid' : task_uuid})

def cmd_note(idx,txt):
    verify_projectdir()
    (ts, note) = get_open_tass()
    ts.reverse()
    task_uuid = ts[idx-1]["uuid"]
    addlog('note',txt,{ 'task_uuid' : task_uuid})
    

    
def get_open_tass():
    orig = readjson()
    tasks = []
    done = set()
    note = {}    
    for t in  orig:
        if t["event"] == "done":
            done.add(t["task_uuid"])
        elif t["event"] == "task" and t["uuid"] not in done:
            tasks.append(t)
        elif t["event"] == "note" and t["uuid"] not in done:
            if t["task_uuid"] not in note:
                note[t["task_uuid"]] = []
            note[t["task_uuid"]].append(t)            

    return (tasks,note)
    


def readjson():
    ( curdir, curprj, linkf ) = get_dirs()
    pf = curdir + "/project-czar.txt"
    txt = open(pf).read()
    if txt == "":
        txt = "[]"
    orig = json.loads(txt)
    return orig


def addlog(ev,notes, add = {}):
    ( curdir, curprj, linkf ) = get_dirs()
    pf = curdir + "/project-czar.txt"
    txt = open(pf).read()
    if txt == "":
        txt = "[]"
    orig = json.loads(txt)
    orig.insert(0, { 'uuid' : str(uuid.uuid4()),
                     'event' : ev,
                     'time'  : datetime.datetime.utcnow().isoformat(),
                     'notes' : notes,
                     **add,
    })
    with open(pf,'w') as out:
        json.dump(orig,out,ensure_ascii=False, indent=2,sort_keys = True)

    
###

if len(sys.argv) < 2 :
    cmd_info()
elif sys.argv[1] in ( 'i', 'info' ) :
    cmd_info()
elif sys.argv[1] in ( '+', 'start' ) :
    cmd_start(sys.argv[2:])
elif sys.argv[1] in ( '-', 'stop' ) :
    cmd_stop(sys.argv[2:])
elif sys.argv[1] in ( 't', 'task' ) :
    cmd_task(sys.argv[2:])
elif sys.argv[1] in ( 'l', 'list' ) :
    cmd_list()
elif sys.argv[1] in ( 'd', 'done' ) :
    cmd_done(int(sys.argv[2]),sys.argv[3:])
elif sys.argv[1] in ( 'n', 'note' ) :
    cmd_note(int(sys.argv[2]),sys.argv[3:])
else:
    cmd_help()


    





