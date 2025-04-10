"""Command line utilities for github"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/01_gh.ipynb.

# %% auto 0
__all__ = ['logger', 'token', 'gh_username', 'api', 'get_token_and_username', 'gh_licenses', 'gh_new_repo_fn', 'gh_new_repo',
           'commit_and_push', 'add_new_branch', 'setup_pages_branch', 'setup_pages_branch_location']

# %% ../nbs/api/01_gh.ipynb 3
from fastcore.all import *
import itertools as it
import os
from ghapi.all import *

import configparser
from pathlib import Path

from .core import *

from warnings import warn
import git
from git import Repo

import logging
logger = logging.getLogger(__name__)

# %% ../nbs/api/01_gh.ipynb 6
def get_token_and_username():
    if "GITHUB_TOKEN" not in os.environ:
        warn("GITHUB_TOKEN is missing")
        return "GITHUB_TOKEN-missing", "username-missing"
    
    token = os.environ["GITHUB_TOKEN"]
    api = GhApi(token=token)
    if 'GITHUB_ACTOR' in os.environ:
        gh_username = "ozpau" # you can't get login name from github workflow
    else:
        gh_username = api.users.get_authenticated()['login']
    return token, gh_username

# %% ../nbs/api/01_gh.ipynb 7
token, gh_username = get_token_and_username()
api = GhApi(owner=gh_username, token=token)

# %% ../nbs/api/01_gh.ipynb 14
@call_parse
def gh_licenses():
    "List GitHub license templates"
    l = api.licenses.get_all_commonly_used(per_page=100)
    #return l.attrgot("spdx_id")
    return "\n".join(l.map(lambda x: f"{pad(x['spdx_id'],16)}{pad(x['name'],42)}"))

# %% ../nbs/api/01_gh.ipynb 16
def gh_new_repo_fn(name, description, license, private):
    gh_repo = api.repos.create_for_authenticated_user(name, description, private=private, license_template=license)
    local_repo = Repo.clone_from(gh_repo.ssh_url, gh_repo.name)
    return gh_repo, local_repo

# %% ../nbs/api/01_gh.ipynb 17
@call_parse
def gh_new_repo(name:str, description:str, license:str="Apache-2.0", private:bool=False):
    "Create a new github repo and clone it"
    gh_new_repo_fn(name, description, license, private)

# %% ../nbs/api/01_gh.ipynb 18
def commit_and_push(repo: Repo, # Repo to commit and push
                    msg: str # Commit message
                   ):
    repo.git.add('.')
    repo.index.commit(msg)
    origin = repo.remote(name='origin')
    origin.push()

# %% ../nbs/api/01_gh.ipynb 27
def add_new_branch(repo: Repo, branch_name: str):
    "Create new branch and push it to upstream"
    head = repo.create_head(branch_name)
    repo.git.push('--set-upstream', 'origin', head)

# %% ../nbs/api/01_gh.ipynb 29
def setup_pages_branch(local_repo: Repo, repo_name: str):
    add_new_branch(local_repo, 'gh-pages')

def setup_pages_branch_location(local_repo: Repo, repo_name: str):
    new_source = {"branch":"gh-pages"}
    try:
        api.repos.create_pages_site(repo_name, source={"branch":"gh-pages"})
    except HTTP409ConflictError:
        api.repos.update_information_about_pages_site(repo_name,
                                                      source={"branch":"gh-pages", "path": "/"})
    api.repos.request_pages_build(repo_name)
