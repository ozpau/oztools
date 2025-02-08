"""Extra command line utilities for nbdev"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/02_nbd.ipynb.

# %% auto 0
__all__ = ['make_things_pretty', 'nbd_new_fn', 'nbd_new', 'new_notebook_template', 'zero_pad', 'nbd_add']

# %% ../nbs/api/02_nbd.ipynb 3
from pathlib import Path
from fastcore.all import *
import itertools as it
import os
from ghapi.all import *

import configparser
from pathlib import Path

from .core import *
from .gh import *

import subprocess

import json

from glob import glob
import re, yaml, shutil
import importlib.resources as res

# %% ../nbs/api/02_nbd.ipynb 5
def make_things_pretty():
    # Fix not being able to click on "source" link in docs
    with open("./nbs/styles.css", 'a') as f: f.write("h3 {\n  width: fit-content;\n}")
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
    setup_pages_branch(local_repo, gh_repo.name)
    os.chdir(gh_repo.name)
    subprocess.run(["nbdev_new"])
    subprocess.run(["nbdev_install_hooks"])
    make_things_pretty()
    subprocess.run(["nbdev_prepare"])
    subprocess.run(["nbdev_clean"])
    subprocess.run(["pip", "install", "-e", ".[dev]"])
    commit_and_push(local_repo, "Initial commit")
    setup_pages_branch_location(local_repo, gh_repo.name)

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
