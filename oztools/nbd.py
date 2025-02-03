"""Extra command line utilities for nbdev"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/02_nbd.ipynb.

# %% auto 0
__all__ = ['nbd_new']

# %% ../nbs/api/02_nbd.ipynb 3
from fastcore.all import *
import itertools as it
import os
from ghapi.all import *

import configparser
from pathlib import Path

from .core import *
from .gh import *
from nbdev.cli import *
from nbdev.clean import *
from nbdev.quarto import *

import subprocess

# %% ../nbs/api/02_nbd.ipynb 4
@call_parse
def nbd_new(name:str, description:str, license:str="Apache-2.0", private:bool=False):
    repo, cloned = gh_new_repo_fn(name, description, license, private)
    os.chdir(repo.name)
    subprocess.run(["nbdev_new"])
    subprocess.run(["nbdev_install_hooks"])
    subprocess.run(["nbdev_prepare"])
    subprocess.run(["nbdev_clean"])
    commit_and_push(cloned, "Initial commit")
    #nbdev_new()
    #nbdev_prepare()
    #nbdev_clean()
