#!/usr/bin/env python3

""" project-czar ,
Manage your projects and tasks

"""

import os
import os.path
import sys

import json

import datetime
import uuid



#""" JSON File Formats
#
#  --X-- project-current:
#     { "project_uuid" : "<uuid> or empty string"
#       "project_directory" : "<absolute_directory>" }
#
#  --X-- project-list:
#     [  {  "project_uuid" : "<uuid>",
#           "project_directory" : "<absolute_directory>" }
#        ...
#     ]
#  --X-- project-<uuid>:
#     [  { "event": "start|stop|task|note|done",
#          "notes" : [ "array" , "of", "strings" ],
#          "time"  : "utcnow().isoformat() .. e.g. 2016-03-31T18:40:03.308473",
#          "uuid"  : "<uuid of this entry>",
#          "task_uuid" : "<uuid of task for note and done event>" },
#         ...
#     ]
#"""

class ProjectCzar:
    """ Provide interface to ~/czar/project-* files """
    ## datadir, curprjfile, listprjfile, curprjjson, listprjjson

    def _prjfile(self, suffix):
        return os.path.join(self.datadir, "project-"+suffix)


    def __init__(self):
        """ use CZAR_HOME or ~/czar  """
        ## The data directory
        self.datadir = os.environ.get("CZAR_HOME", None)
        if not self.datadir:
            self.datadir = os.path.join(os.environ["HOME"], "czar")
        ## Not sure if these fields are good idea...
        self.curprjfile = self._prjfile("current")
        self.listprjfile = self._prjfile("list")
        self.curprjjson = self.load('current', {})
        self.listprjjson = self.load('list', [])

    def save(self, suff, obj):
        """Save the obj in the project-<suff> file"""
        with open(self._prjfile(suff), "w") as wfd:
            json.dump(obj, wfd, ensure_ascii=False, indent=2, sort_keys=True)

    def load(self, suff, default=None):
        """ Load, or return default if not found """
        fullname = self._prjfile(suff)
        try:
            with open(fullname, "r") as rfd:
                return json.load(rfd)
        except IOError:
            return default


    def project_of_directory(self, folder=None):
        """ return project associated with given directory, or cwd"""
        if not folder:
            folder = os.getcwd()
        prj = self.lookup_project_by_dir(folder)
        if prj:
            return prj
        else:
            return None

    def current_project(self):
        """ return currently active project, if any """
        return self.curprjjson if len(self.curprjjson) > 0 else None


    def is_path_below(self, root, below):
        """ /a, /a/* => True, /a, /b => False"""
        r = os.path.relpath(below, root)
        if r == '.':
            return True
        if r[0] == '.':
            return False
        return True

    def lookup_project_by_dir(self, indir):
        """indir can be a sub-dir of prjdir too !!"""
        prjs = []
        for p in self.listprjjson:
            if self.is_path_below(p["project_directory"], indir):
                prjs.append(p)
        if len(prjs) == 0:
            return None
        if len(prjs) == 1:
            return prjs[0]
        tell("**Internal Error: ", indir, " claimed by multiple projects:",
             ' '.join([x["project_directory"] for x in prjs]))
        sys.exit(1)

    def get_open_task(self, prj):
        orig = self.load(prj["project_uuid"], {})
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

        return (tasks, note)

    def addlog(self, prj, ev, notes, add=None):
        obj = self.load(prj["project_uuid"], [])
        if not add:
            add = {}
        obj.insert(0, {'uuid' : str(uuid.uuid4()),
                       'event' : ev,
                       'time'  : datetime.datetime.utcnow().isoformat(),
                       'notes' : notes,
                       **add})
        self.save(prj["project_uuid"], obj)

    def which_project(self):
        prjdir = self.project_of_directory()
        curprj = self.current_project()
        if prjdir is None:
            if curprj is None:
                tell("** ERROR: No project active, and current directory not a project")
                return None
            else:
                tell("** WARNING: Current directory not a project, showing:",
                     curprj["project_directory"])
                return curprj
        else:
            if curprj is None:
                tell("** WARNING: No active project, showing current directory: ",
                     prjdir["project_directory"])
                return prjdir
            else:
                if prjdir == curprj:
                    return prjdir
                else:
                    tell("** ERROR : Current Directory NOT under active project")
                    return None


    def cmd_add(self, in_prjdir):
        """ Bring new project under czar """
        prjdir = os.path.realpath(in_prjdir)
        existing_project = self.lookup_project_by_dir(prjdir)
        if existing_project:
            tell("The project ", existing_project["project_directory"],
                 " is already under czar")
        else:
            newid = str(uuid.uuid4())
            self.listprjjson.append({"project_uuid" : newid,
                                     "project_directory" : prjdir})
            self.save('list', self.listprjjson)
            self.save(newid, [])

    def cmd_list(self):
        showprj = self.which_project()
        if showprj:
            (tasks, notes) = self.get_open_task(showprj)
            tasks.reverse()
            idx = 1
            for t in tasks:
                print(idx, ' -- ', ' '.join(t["notes"]))
                if t["uuid"] in notes:
                    for n in notes[t["uuid"]]:
                        print("        ", ' '.join(n["notes"]))
                idx = idx + 1

    def cmd_done(self, idx, txt):
        showprj = self.which_project()
        if showprj:
            tasks = self.get_open_task(showprj)[0]
            tasks.reverse()
            task_uuid = tasks[idx-1]["uuid"]
            self.addlog(showprj, 'done', txt, {'task_uuid' : task_uuid})

    def cmd_note(self, idx, txt):
        showprj = self.which_project()
        if showprj:
            tasks = self.get_open_task(showprj)[0]
            tasks.reverse()
            task_uuid = tasks[idx-1]["uuid"]
            self.addlog(showprj, 'note', txt, {'task_uuid' : task_uuid})

    def cmd_task(self, txt):
        showprj = self.which_project()
        if showprj:
            self.addlog(showprj, 'task', txt)

    def cmd_start(self, txt):
        prjdir = self.project_of_directory()
        if prjdir is None:
            tell("**ERROR: Not in a project directory")
            return
        curprj = self.current_project()
        if curprj:
            if prjdir["project_uuid"] == curprj["project_uuid"]:
                tell("Project already running")
            else:
                tell("**ERROR: Project ", curprj["project_directory"], " running. stop it.")
            return
        self.save("current", prjdir)
        self.addlog(prjdir, 'start', txt)

    def cmd_stop(self, txt):
        curprj = self.current_project()
        if curprj:
            self.save("current", {})
            self.addlog(curprj, 'stop', txt)
        else:
            tell("**ERROR No active project")

    def cmd_info(self):
        self.which_project()




################################################################################

def tell(*args):
    print(*["%s"%x for x in args], ';')

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

###


pc = ProjectCzar()

#elif sys.argv[1] in ( 'p', 'pend','pending' ) :
#    cmd_pending('/data/Projects')

if len(sys.argv) < 2:
    pc.cmd_info()
elif sys.argv[1] in ('i', 'info'):
    pc.cmd_info()
elif sys.argv[1] in ('d', 'done'):
    pc.cmd_done(int(sys.argv[2]), sys.argv[3:])
elif sys.argv[1] in ('t', 'task'):
    pc.cmd_task(sys.argv[2:])
elif sys.argv[1] in ('-', 'stop'):
    pc.cmd_stop(sys.argv[2:])
elif sys.argv[1] in ('+', 'start'):
    pc.cmd_start(sys.argv[2:])
elif sys.argv[1] in ('n', 'note'):
    pc.cmd_note(int(sys.argv[2]), sys.argv[3:])
elif sys.argv[1] in ('a', 'add'):
    pc.cmd_add(os.getcwd())
elif sys.argv[1] in ('l', 'list'):
    pc.cmd_list()
else:
    cmd_help()

## End




