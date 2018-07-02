
#!/usr/bin/python -Bu
#
# Copyright (c) 2016 Nutanix Inc. All rights reserved.
#
# Author: bfinn@nutanix.com
#
# Whitelist management API
#

import cherrypy
import json
import time

from threading import RLock


class WhitelistEntriesAPI(object):
  exposed = True

  def __init__(self, opts, args):
    self.whitelist_lock = RLock()
    self.whitelist_fname = opts.output_whitelist_fname
    self.whitelist = {}
    self._read_whitelist(opts.seed_whitelist_fname)

  def _read_whitelist(self, whitelist=None):
    fname = whitelist or self.whitelist_fname
    with self.whitelist_lock:
      with open(fname, "r") as fh:
        self.whitelist = json.load(fh)["iso_whitelist"]

  def _write_whitelist(self):
    """
    I will call this from methods already protected by a lock, but since python
    doesn't let me make this properly private, I am protecting it and making
    whitelist_lock an RLock.

    Obviously, this is optimized for simplicity and correctness rather than
    performance.
    """
    with self.whitelist_lock:
      try:
        with open(self.whitelist_fname, "w") as fh:
          json.dump(self.get_entire_whitelist(), fh, indent=2)
          fh.flush()
      except Exception as e:
        raise cherrypy.HTTPError(500, "Failed to commit an update with error "
          "%s. Please retry the operation that failed. If it fails again, "
          "check that the current user has permission to write to the "
          "backing file %s" % (e, self.whitelist_fname))

  def get_entire_whitelist(self):
    return {
        "last_modified": int(time.time()),
        "iso_whitelist": self.whitelist
      }

  def get_validated_whitelist(self):
    validated_entries = {}
    for checksum, entry in self.whitelist.iteritems():
      if entry.get("validated", False):
        validated_entries[checksum] = entry
    return {
        "last_modified": int(time.time()),
        "iso_whitelist": validated_entries
      }

  def get_keys(self):
    with self.whitelist_lock:
      return self.whitelist.keys()

  def get_entry(self, checksum):
    with self.whitelist_lock:
      if checksum in self.whitelist:
        return self.whitelist[checksum]
      else:
        return None

  def add_entry(self, checksum, body):
    with self.whitelist_lock:
      # TODO validate
      if checksum in self.whitelist:
        return (400, "Checksum %s already exists" % checksum)
      self.whitelist[checksum] = body
      self._write_whitelist()
    return 200, ""

  def update_entry(self, checksum, body):
    with self.whitelist_lock:
      # TODO validate
      if not checksum in self.whitelist:
        return (404, "Checksum %s does not exist" % checksum)
      self.whitelist[checksum] = body
      self._write_whitelist()
    return 200, ""

  def delete_entry(self, checksum):
    with self.whitelist_lock:
      # TODO validate
      if not checksum in self.whitelist:
        return (404, "Checksum %s does not exist" % checksum)
      del self.whitelist[checksum]
      self._write_whitelist()
    return 200, ""

  @cherrypy.tools.json_out()
  def GET(self, checksum=None):
    if not checksum:
      return self.get_keys()
    entry = self.get_entry(checksum)
    if entry:
      return entry
    else:
      raise cherrypy.HTTPError(404, "Installer checksum %s does not exist" %
        checksum)

  @cherrypy.tools.json_in()
  def POST(self, checksum):
    code, complaint = self.add_entry(checksum, cherrypy.request.json)
    if code != 200:
      raise cherrypy.HTTPError(code, complaint)

  @cherrypy.tools.json_in()
  def PUT(self, checksum):
    code, complaint = self.update_entry(checksum, cherrypy.request.json)
    if code != 200:
      raise cherrypy.HTTPError(code, complaint)

  def DELETE(self, checksum):
    code, complaint = self.delete_entry(checksum)
    if code != 200:
      raise cherrypy.HTTPError(code, complaint)
