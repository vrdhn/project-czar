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

class Color:
    """ Just some colors for vt100 """
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


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
        partial_path = os.path.relpath(below, root)
        if partial_path == '.':
            return True
        if partial_path[0] == '.':
            return False
        return True

    def lookup_project_by_dir(self, indir):
        """indir can be a sub-dir of prjdir too !!"""
        prjs = []
        for idxp in self.listprjjson:
            if self.is_path_below(idxp["project_directory"], indir):
                prjs.append(idxp)
        if len(prjs) == 0:
            return None
        if len(prjs) == 1:
            return prjs[0]
        tell("**Internal Error: ", indir, " claimed by multiple projects:",
             ' '.join([x["project_directory"] for x in prjs]))
        sys.exit(1)

    def get_open_task(self, prj):
        """ get open tasks and note """
        orig = self.load(prj["project_uuid"], {})
        tasks = []
        done = set()
        note = {}
        for idxt in  orig:
            if idxt["event"] == "done":
                done.add(idxt["task_uuid"])
            elif idxt["event"] == "task" and idxt["uuid"] not in done:
                tasks.append(idxt)
            elif idxt["event"] == "note" and idxt["uuid"] not in done:
                if idxt["task_uuid"] not in note:
                    note[idxt["task_uuid"]] = []
                note[idxt["task_uuid"]].append(idxt)

        return (tasks, note)

    def addlog(self, prj, evt, notes, add=None):
        """ Add a event-log to project file"""
        obj = self.load(prj["project_uuid"], [])
        if not add:
            add = {}
        obj.insert(0, {'uuid' : str(uuid.uuid4()),
                       'event' : evt,
                       'time'  : datetime.datetime.utcnow().isoformat(),
                       'notes' : notes,
                       **add})
        self.save(prj["project_uuid"], obj)

    def which_project(self):
        """ which project .. active or current TODO: this needs fixing"""
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
        """ list the tasks and notes """
        showprj = self.which_project()
        if showprj:
            self.aux_list(showprj)

    def aux_list(self, prj, indent=''):
        """ print tasks and notes"""
        (tasks, notes) = self.get_open_task(prj)
        tasks.reverse()
        idx = 1
        for idxt in tasks:
            print(indent, '[%d]'%idx, ' '.join(idxt["notes"]), '.')
            if idxt["uuid"] in notes:
                for idxn in notes[idxt["uuid"]]:
                    print(indent, "  + ", ' '.join(idxn["notes"]), '.')
            idx = idx + 1

    def cmd_done(self, idx, txt):
        """ mark a task done """
        showprj = self.which_project()
        if showprj:
            tasks = self.get_open_task(showprj)[0]
            tasks.reverse()
            task_uuid = tasks[idx-1]["uuid"]
            self.addlog(showprj, 'done', txt, {'task_uuid' : task_uuid})

    def cmd_note(self, idx, txt):
        """ add note to task """
        showprj = self.which_project()
        if showprj:
            tasks = self.get_open_task(showprj)[0]
            tasks.reverse()
            task_uuid = tasks[idx-1]["uuid"]
            self.addlog(showprj, 'note', txt, {'task_uuid' : task_uuid})

    def cmd_task(self, txt):
        """ add task to project """
        showprj = self.which_project()
        if showprj:
            self.addlog(showprj, 'task', txt)

    def cmd_start(self, txt):
        """ clock-in a project """
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
        """ clock-out a project """
        curprj = self.current_project()
        if curprj:
            self.save("current", {})
            self.addlog(curprj, 'stop', txt)
        else:
            tell("**ERROR No active project")

    def cmd_info(self):
        """ some info """
        prj = self.which_project()
        if prj:
            tell("Active Project: ", prj["project_directory"])
            self.aux_list(prj, '')

    def cmd_pending(self):
        """ pending list .. tasks/notes of all projects"""
        for idxp in self.listprjjson:
            tell(">", Color.BOLD,
                 os.path.basename(idxp["project_directory"]),
                 Color.END)
            self.aux_list(idxp, '   ')


################################################################################

def tell(*args):
    """ just a tell """
    print(*["%s"%x for x in args])

def cmd_help():
    """ help ..."""
    tell(". Project - Czar Usage:")
    tell(".     i                  -- info ")
    tell(".     a,add              -- add a project to czar ")
    tell(".     +,start <txt>      -- start clock")
    tell(".     -,stop  <txt>      -- stop clock")
    tell(".     t,task  <txt>      -- add a task to do")
    tell(".     l,list             -- list tasks")
    tell(".     d,done  <d> <txt>  -- mark  task done")
    tell(".     n,note  <d> <txt>  -- add note to  task")
    tell(".     p,pending          -- show tasks of all projects")

###


def main():
    """ just main """
    curprj = ProjectCzar()

    if len(sys.argv) < 2:
        curprj.cmd_info()
    elif sys.argv[1] in ('i', 'info'):
        curprj.cmd_info()
    elif sys.argv[1] in ('d', 'done'):
        curprj.cmd_done(int(sys.argv[2]), sys.argv[3:])
    elif sys.argv[1] in ('t', 'task'):
        curprj.cmd_task(sys.argv[2:])
    elif sys.argv[1] in ('-', 'stop'):
        curprj.cmd_stop(sys.argv[2:])
    elif sys.argv[1] in ('+', 'start'):
        curprj.cmd_start(sys.argv[2:])
    elif sys.argv[1] in ('n', 'note'):
        curprj.cmd_note(int(sys.argv[2]), sys.argv[3:])
    elif sys.argv[1] in ('a', 'add'):
        curprj.cmd_add(os.getcwd())
    elif sys.argv[1] in ('l', 'list'):
        curprj.cmd_list()
    elif sys.argv[1] in ('p', 'pend', 'pending'):
        curprj.cmd_pending()
    else:
        cmd_help()


main()
## End




