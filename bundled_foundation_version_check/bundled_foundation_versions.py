#!/usr/bin/python

import json
import os
import re
import subprocess
import sys

from pprint import pformat

VERSION_RE = re.compile(r"\s+\S+-(\d(?:\.\d){1,3})-stable$")
TOP = os.getenv("TOP")

def git(cmd):
  proc = subprocess.Popen("git %s" % cmd, shell=True, stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
  out, err = proc.communicate()
  ret = proc.returncode
  if ret != 0:
    raise StandardError("Command \"%s\" failed with ret %d, out:\n%s\nerr:\n%s"
      % (cmd, ret, out, err))
  return out, err

def get_all_branches(min_version=[4,5]):
  out, _ = git("branch -r")
  branches = []
  for branch in out.splitlines():
    match = VERSION_RE.search(branch)
    if match:
      version = [int(digit) for digit in match.group(1).split(".")]
      if version >= min_version:
        branches.append(branch)
  return branches

def get_version_for_branch(branch):
  """
  Conveniently, all the components we're looking for have a line of roughly the
  form "THING_VERSION := wibble".
  """
  contents, _ = git("show %s:Makefile.installer" % branch)
  line_start = {
    "foundation": "FOUNDATION_BUILD_VERSION",
    "ahv": "AHV_VERSION",
    "ncc": "NCC_VERSION",
    }
  ver = {}
  components_found = 0
  for line in contents.splitlines():
    for component, signature in line_start.iteritems():
      if line.startswith(signature):
        ver[component] = line.split("=")[-1].strip()
        components_found += 1
      if components_found == len(line_start):
        break

  return ver

def get_all_foundation_versions():
  branches = get_all_branches()
  versions = {}
  for branch in branches:
    version = get_version_for_branch(branch)
    print("%s - %s" % (branch, pformat(version)))
    # Remove remote from key for readability.
    versions[branch.split("/", 1)[-1]] = version
  return versions

if __name__ == "__main__":
  git("fetch")
  versions = get_all_foundation_versions()

  fname = "bundled_versions.json"
  with open(fname, "w") as fh:
    json.dump(versions, fh, indent=2)
  print("wrote results to %s" % fname)
