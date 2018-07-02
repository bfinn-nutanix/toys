#!/usr/bin/python -Bu
#
# Copyright (c) 2016 Nutanix Inc. All rights reserved.
#
# Author: bfinn@nutanix.com
#
# API managing whitelist files and git
#

import cherrypy
import json
import logging
import os
import subprocess
import tempfile
import time
import whitelist_api

from threading import Lock

WHITELIST_PATH = "foundation/config/iso_whitelist.json"

class FileAPI(object):

  def __init__(self, whitelist_instance, opts, args):
    self.whitelist_instance = whitelist_instance
    self.root = opts.repo_root
    self.repo_lock = Lock()
    self.original_dir = os.getcwd()
    self.unit_test_mode = opts.unit_test_mode
    with self.repo_lock:
      # TODO handle errors
      out, err, ret = self.git(["checkout", "master"])
      out, err, ret = self.git(["pull"])

  def system(self, cmd_list, timeout=60):
    stdout = ""
    stderr = ""
    return_code = -1
    try:
      process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
      stdout, stderr = process.communicate(timeout=timeout)
      return_code = process.returncode
    except subprocess.TimeoutExpired:
      logging.error("Command '%s' timed out" % command)
      process.kill()
      process.wait()
      return_code = process.returncode
    except OSError as e:
      logging.exception("Could not execute '%s': %s" % (command, e))
      return_code = -1

    if return_code != 0:
      message = "Command '%s' returned error code %d\n" % (
          " ".join(cmd_list), return_code)
      message += "stdout:\n%s\nstderr:\n%s" % (stdout, stderr)
      logging.error(message)
    return stdout, stderr, return_code

  def git(self, cmd_list, timeout=60):
    try:
      os.chdir(self.root)
      git_cmd = ["git"] + cmd_list
      return self.system(git_cmd, timeout)
    finally:
      os.chdir(self.original_dir)

  def push_to_gerrit(self):
    try:
      os.chdir(self.root)
      if self.unit_test_mode:
        gerrit_cmd = ["upload-gerrit", "drafts", "master"]
      else:
        gerrit_cmd = ["upload-gerrit", "patch", "master"]
      return self.system(gerrit_cmd)
    finally:
      os.chdir(self.original_dir)

  @cherrypy.expose
  def get_whitelist_as_file(self, only_validated=False):
    if only_validated:
      whitelist = self.whitelist_instance.get_validated_whitelist()
    else:
      whitelist = self.whitelist_instance.get_entire_whitelist()
    tf = tempfile.TemporaryFile()
    json.dump(whitelist, tf, indent=2)
    tf.seek(0)
    return cherrypy.lib.static.serve_fileobj(tf,
      content_type="application/x-download")

  @cherrypy.expose
  def push_validated_whitelist_to_gerrit(self):
    # TODO handle errors
    with self.repo_lock:
      out, err, ret = self.git(["checkout", "master"])
      out, err, ret = self.git(["pull"])
      whitelist = self.whitelist_instance.get_validated_whitelist()
      target_path = os.path.join(self.root, WHITELIST_PATH)
      with open(target_path, "w") as fh:
        json.dump(whitelist, fh, indent=2)
      out, err, ret = self.git(["add", target_path])
      out, err, ret = self.git(["commit", "-m", "Update whitelist to %s" %
        whitelist["last_modified"]])
      out, err, ret = self.push_to_gerrit()
      commit_msg, err, ret = self.git(["log", "HEAD", "-n", "1"])
      out, err, ret = self.git(["reset", "--hard", "HEAD~"])
    return commit_msg

