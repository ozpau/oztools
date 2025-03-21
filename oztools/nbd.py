"""Extra command line utilities for nbdev"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/02_nbd.ipynb.

# %% auto 0
__all__ = ['make_things_pretty', 'nbd_new_fn', 'nbd_new', 'new_notebook_template', 'zero_pad', 'nbd_add',
           'get_directories_recursive', 'watch_new_directories', 'extract_exports', 'get_hash', 'setup_tracking',
           'inotify_watch', 'get_files_updated', 'anything_updated', 'nbd_watch']

# %% ../nbs/api/02_nbd.ipynb 3
from pathlib import Path
from fastcore.all import *
import itertools as it
import os, time
from ghapi.all import *

import configparser
from pathlib import Path

from .core import *
from .gh import *

import subprocess

import json
from fastcore.net import HTTP422UnprocessableEntityError

from glob import glob
import re, yaml, shutil
import importlib.resources as res

import asyncio
from asyncinotify import Inotify, Event, Mask
from pathlib import Path
from datetime import datetime

import hashlib

# %% ../nbs/api/02_nbd.ipynb 5
def make_things_pretty():
    # Fix not being able to click on "source" link in docs
    with open("./nbs/styles.css", 'a') as f: f.write("\nh3 {\n  width: fit-content;\n}")
    # Add dark theme and make bright theme compatible with in in colorscheme
    theme = {'light': 'united', 'dark': 'superhero'}
    with open("./nbs/_quarto.yml", 'r') as f: data = yaml.safe_load(f)
    data['format']['html']['theme'] = theme
    data['website']['favicon'] = 'favicon.png'
    with open("./nbs/_quarto.yml", 'w') as f: f.write(yaml.dump(data))
    # Copy favicon
    with res.as_file(res.files("oztools")/"data/favicon.png") as f: shutil.copy(f, "./nbs")

# %% ../nbs/api/02_nbd.ipynb 6
def nbd_new_fn(name:str, description:str, license:str="Apache-2.0", private:bool=False):
    "Create a new nbdev project and setup github repo for it"
    gh_repo, local_repo = gh_new_repo_fn(name, description, license, private)
    # this one makes github run CI twice (not nice)
    #setup_pages_branch(local_repo, gh_repo.name)
    os.chdir(gh_repo.name)
    subprocess.run(["nbdev_new"]) # TODO: use .__wrapped__ property to extract original function
    subprocess.run(["nbdev_install_hooks"])
    make_things_pretty()
    subprocess.run(["nbdev_prepare"])
    subprocess.run(["nbdev_clean"])
    # Hopefully using pip + some sleep would be enough for github to be ready
    # to enable pages branch
    commit_and_push(local_repo, "Initial commit")
    subprocess.run(["pip", "install", "-e", ".[dev]"])
    print("Waiting for the github to finish build before enabling pages")
    print("Feel free to start working on the project")
    # TODO: maybe check github api if build is ready
    while True:
        time.sleep(20)
        try:
            setup_pages_branch_location(local_repo, gh_repo.name)
            break
        except HTTP422UnprocessableEntityError:
            pass

# %% ../nbs/api/02_nbd.ipynb 7
@call_parse
def nbd_new(name:str, description:str, license:str="Apache-2.0", private:bool=False):
    "Create a new nbdev project and setup github repo for it"
    nbd_new_fn(name, description, license, private)

# %% ../nbs/api/02_nbd.ipynb 8
def new_notebook_template(name, description):
    template = {
        'cells': [
            {'cell_type': 'markdown', 'metadata': {},
             'source': [
                    f'# {name}\n',
                    '\n',
                    f'> {description}'
                ]},
            {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [],
             'source': [f'#| default_exp {name}']},
            {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [],
             'source': [
                 '#| hide\n',
                 'from nbdev.showdoc import *'
             ]},
            {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [],
             'source': [
                 '#| export\n',
                 'from fastcore.all import *'
             ]},
            {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [],
             'source': [
                 '#| hide\n',
                 'import nbdev; nbdev.nbdev_e'+'xport()' # nbdev_e**ort is a forbidden word
             ]},
      ], 'metadata': { 'kernelspec': { 'display_name': 'python3', 'language': 'python', 'name': 'python3' } }, 'nbformat': 4, 'nbformat_minor': 4
    }
    return template

# %% ../nbs/api/02_nbd.ipynb 12
def zero_pad(num):
    num = str(num)
    return num if len(num) > 1 else f"0{num}"

# %% ../nbs/api/02_nbd.ipynb 14
@call_parse
def nbd_add(name:str, description:str,
            at:Optional[int] = None # If specified, insert new notebook at a specific position
           ):
    "Add new notebook to the project"

    prev_nbs = L(glob("[0-9]*?*.ipynb"))
    prev_ids = prev_nbs.map(lambda x: int(re.match(r'(\d+).*\.ipynb', x).group(1)))
    prev_id = max(prev_ids)

    new_id = prev_id + 1
    new_id = zero_pad(new_id)
    template = new_notebook_template(name, description)

    with open(f"{new_id}_{name}.ipynb", 'w') as f:
        json.dump(template, f)

# %% ../nbs/api/02_nbd.ipynb 17
def get_directories_recursive(path: Path):
    return (Path(d) for d,_,_ in os.walk(path))

# %% ../nbs/api/02_nbd.ipynb 20
def watch_new_directories(inotify, event):
    if Mask.CREATE in event.mask and event.path is not None and event.path.is_dir():
        for directory in get_directories_recursive(event.path): inotify.add_watch(directory, mask)

# %% ../nbs/api/02_nbd.ipynb 21
def extract_exports(file):
    return '\n'.join([
        ''.join(x['source']) for x in file.read_json()['cells']
        if x['cell_type'] == 'code' and 'export' in ''.join(x['source'])
    ])

# %% ../nbs/api/02_nbd.ipynb 22
def get_hash(s):
    h_func = hashlib.sha256(s.encode("utf-8"))
    return h_func.digest()

# %% ../nbs/api/02_nbd.ipynb 24
def setup_tracking(path):
    files = dict()
    for d in get_directories_recursive(path):
        if d.name == '.ipynb_checkpoints':
            continue
        for f in d.ls():
            if not re.match(r'^(?!\.\~).+\.ipynb$', f.name):
                continue
            files[f] = get_hash(extract_exports(f))
    return files

# %% ../nbs/api/02_nbd.ipynb 33
def _inotify_watch(inotify, path, debounce_interval):
    mask = (Mask.CREATE | Mask.MODIFY | Mask.MOVE | Mask.CLOSE_WRITE
            | Mask.DELETE | Mask.DELETE_SELF | Mask.ATTRIB)
    for directory in get_directories_recursive(path): inotify.add_watch(directory, mask)

    combined_event = []
    def process_event(event):
        watch_new_directories(inotify, event)
        if not event.mask & mask: return False
        combined_event.append(event)
        return True

    while True:
        inotify.sync_timeout=-1 # Watch forever
        for event in inotify:
            if not process_event(event): continue

            inotify.sync_timeout = debounce_interval
            for event_seq in inotify:
                if not process_event(event): continue

            # No more events seen in sync_timeout: yield events seen in this event sequence
            if combined_event:
                yield combined_event
                combined_event = []

# %% ../nbs/api/02_nbd.ipynb 34
def inotify_watch(path, debounce_interval=0.5):
    with Inotify() as inotify:
        yield from _inotify_watch(inotify, path, debounce_interval)

# %% ../nbs/api/02_nbd.ipynb 39
def get_files_updated(events):
    unique = set((e.watch.path, e.name.name) for e in events)
    ipynb = ((path, re.match(r'\.\~(.*.ipynb)', name)) for path, name in unique)
    ipynb = [path/name.group(1) for path, name in ipynb if name]
    return ipynb

# %% ../nbs/api/02_nbd.ipynb 42
def anything_updated(tracked_files, events):
    updated = []
    for filename in get_files_updated(events):
        new_hash = get_hash(extract_exports(filename))
        if new_hash != tracked_files[filename]:
            updated.append(filename)
            tracked_files[filename] = new_hash
    return updated

# %% ../nbs/api/02_nbd.ipynb 43
def nbd_watch():
    "Watch `nbs` folder and automatically run `nbdev_export` on file change"

    path = Path('nbs')
    tracked_files = setup_tracking(path)

    for events in inotify_watch(path):
        # filter events
        # - ignore temporary file saves (this happens automatically, and we don't
        #   want to refresh anything unless user explicitly saves a file)
        if len(events) < 13: continue

        updated = anything_updated(tracked_files, events)
        if not updated: continue

        #for e in events: print(e)
        print(f"[{datetime.now()}] {' '.join(p.relative_to(Path('nbs')).as_posix() for p in updated)}")
        subprocess.run(["nbdev_export"])
