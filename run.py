#! /usr/bin/env python

from os import access, listdir, X_OK
from os.path import abspath, isfile, join as pathjoin
from subprocess import Popen

def run(executable, options, cwd):
    return Popen([executable] + options, cwd=cwd)

def abspath_listdir(d):
    return [abspath(pathjoin(d, name)) for name in listdir(d)]

def is_executable_file(f):
    return isfile(f) and access(f, X_OK)

def find_executable(d):
    return filter(is_executable_file, abspath_listdir(d))[0]

def run_component(component_dir, options):
    executable = find_executable(component_dir)
    proc = run(executable, options, component_dir)
    print '%s running with pid %d' % (component_dir, proc.pid)
    return proc

procs = [run_component(c, []) for c in abspath_listdir('components')]
raw_input('Press Enter to stop components')
for p in procs:
    p.kill()
