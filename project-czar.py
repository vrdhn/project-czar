#!/usr/bin/env python3


import os
import os.path
import sys

import pathlib
import json

import datetime
import uuid



""" JSON File Formats

  --X-- project-current:
     { "project_uuid" : "<uuid> or empty string" }
 
  --X-- project-list:
     [  {  "project_uuid" : "<uuid>",
           "project_directory" : "<absolute_directory>" }
        ...
     ]
  --X-- project-<uuid>:
     [  { "event": "start|stop|task|note|done",
          "notes" : [ "array" , "of", "strings" ],
          "time"  : "utcnow().isoformat() .. e.g. 2016-03-31T18:40:03.308473",
          "uuid"  : "<uuid of this entry>",
          "task_uuid" : "<uuid of task for note and done event>" },
         ...
     ]
"""

class ProjectCzar:
    """ Provide interface to ~/czar/project-* files """
    ## datadir, curprjfile, listprjfile, curprjjson, listprjjson

    def _prjfile(self, x):
        return os.path.join(self.datadir,"project-"+x)
                

    def __init__(self):
        """ use CZAR_HOME or ~/czar  """
        ## The data directory
        self.datadir = os.environ.get("CZAR_HOME",None)        
        if not self.datadir:
            self.datadir = os.path.join(os.environ["HOME"],"czar")
        ## root files
        self.curprjfile = self._prjfile("current")
        self.listprjfile = self._prjfile("list")
        ## first root object
        if not os.path.isdir(self.datadir):
            os.makedirs(self.datadir)
        if not os.path.isfile(self.curprjfile):
            with open(self.curprjfile,'w') as fd:
                fd.write('{}')
            self.curprjjson = json.loads('{}')
        else:
            with open(self.curprjfile) as fd:
                self.curprjjson = json.loads(fd.read())
        ## and another root object...
        if not os.path.isfile(self.listprjfile):
            with open(self.listprjfile,'w') as fd:
                fd.write('[]')
                self.listprjjson = json.loads('[]')
        else:
            with open(self.listprjfile) as fd:
                self.listprjjson = json.loads(fd.read())

    def save(self, suff, obj):
        with open(self._prjfile(suff),"w") as fd:
            json.dump(obj,fd,ensure_ascii=False, indent=2,sort_keys = True)
        
            
    def project_of_directory(self, dir = None):
        """ return project associated with given directory, or cwd"""
        if not dir:
            dir = os.getcwd()
        ### 

    def current_project(self):
        """ return currently active project, if any """

    def is_path_below( self, root, below):
        """ /a, /a/* => True, /a, /b => False"""
        r = os.path.relpath(below,root)
        if r == '.':
            return True
        if r[0] == '.':
            return False
        return True

    def lookup_project_by_dir(self, indir):
        """indir can be a sub-dir of prjdir too !!"""
        prjs = []
        for p in self.listprjjson:
            if self.is_path_below(p["project_directory"],indir):
                prjs.append(p)
        if len(prjs) == 0:
            return None
        if len(prjs) == 1:
            return prjs[0]
        tell("**Internal Error: ", indir, " claimed by multiple projects:" ,
             ' '.join([x["project_directory"] for x in prjs]))
        sys.exit(1)
            

    def cmd_add(self,in_prjdir):
        """ Bring new project under czar """
        prjdir = os.path.realpath(in_prjdir)
        existing_project = self.lookup_project_by_dir(prjdir)
        if existing_project:
            tell("The project ", existing_project["project_directory"],
                 " is already under czar")
        else:
            newid = str(uuid.uuid4())
            self.listprjjson.append( { "project_uuid" : newid,
                                       "project_directory" : prjdir } )
            self.save('list',self.listprjjson)
            self.save(newid,[])
            

################################################################################                

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
    tell(".     i         -- info ")
    tell(".     a,add     -- add a project to czar ")
    tell(".     +,start   -- start clock")
    tell(".     -,stop    -- stop clock")
    tell(".     t,task    -- add a task to do")
    tell(".     l,list    -- list tasks")
    tell(".     d,done    -- mark # task done")
    tell(".     n,note    -- add note to # task")
    tell(".     p,pending -- show tasks of all projects")


        
    
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


pc = ProjectCzar()

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
elif sys.argv[1] in ( 'p', 'pend','pending' ) :
    cmd_pending('/data/Projects')
elif sys.argv[1] in ( 'a', 'add' ) :
    pc.cmd_add(os.getcwd())
else:
    cmd_help()


    





