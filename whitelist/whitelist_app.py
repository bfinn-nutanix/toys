#!/usr/bin/python -Bu
#
# Copyright (c) 2016 Nutanix Inc. All rights reserved.
#
# Author: bfinn@nutanix.com
#
# HTTP server for maintaining the installer whitelist
#

import cherrypy
import logging
import optparse
import os
import time
import file_api
import whitelist_api

HTTP_PORT = 9000
HTTP_SERVER_THREADS = 10
UNIT_TEST_MODE = False

class HTTPRoot(object):
  @cherrypy.expose
  def index(self):
    raise cherrypy.HTTPRedirect("gui/app/views/entry_list.html", 302)

  @cherrypy.expose
  def alive(self):
    """
    This dummy function enables callers to block until the server is responding
    to requests properly.
    """
    pass

class GuiRoot(object):
  pass

def patch_cherrypy_static_no_cache():
  """
  Patch cptools.validate_since to NOP and add cache control headers to response
  """
  def skip_validate_since_and_add_headers():
    response = cherrypy.serving.response
    # HTTP 1.1.
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    # HTTP 1.0.
    response.headers["Pragma"] = "no-cache"
    # Proxies.
    response.headers["Expires"] = "0"

  cherrypy.lib.cptools.validate_since = skip_validate_since_and_add_headers

def create(options, args):
  """
    Start HTTP server. Returns a reference to cherrypy's tree so that the
    caller can add additional apps.
  """

  patch_cherrypy_static_no_cache()

  cherrypy.config.update(
    {
     "server.socket_host": "::",
     "server.socket_port": HTTP_PORT,
     "server.thread_pool": HTTP_SERVER_THREADS,
     "server.max_request_body_size": 8 * (2 ** 30),  # uploads should be < 8G.
     "engine.autoreload.on": False,
    })

  cherrypy.tree.mount(root=HTTPRoot(),
    script_name="/",
    config = {})

  gui_root_config = {
    "/":
      {
        "tools.staticdir.root": os.path.abspath(os.path.dirname(__file__)),
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "gui"
      },
  }
  cherrypy.tree.mount(root=GuiRoot(),
                      script_name="/gui",
                      config=gui_root_config)

  whitelist_api_instance = whitelist_api.WhitelistEntriesAPI(options, args)
  cherrypy.tree.mount(root=whitelist_api_instance,
    script_name="/api/entries",
    config = {
      "/": {
        "request.dispatch": cherrypy.dispatch.MethodDispatcher()
      }
    })

  cherrypy.tree.mount(
    root=file_api.FileAPI(whitelist_api_instance, options, args),
    script_name="/api/file")

  return cherrypy.tree

def start():
  cherrypy.engine.start()

def block():
  cherrypy.engine.block()  # Waits forever.

def stop():
  cherrypy.engine.exit()

def daemon_loop():
  while True:
    time.sleep(0.1)

def main(options, args):
  try:
    create(options, args)
    start()
    daemon_loop()
  except:
    logging.exception("Unexpected exception")
  finally:
    stop()

def service(options, args):
  import daemon
  log_file = open("service_log", "w")

  with daemon.DaemonContext(
      stdout=log_file,
      stderr=log_file,
      working_directory=os.getcwd()):
    main(options, args)

def parse_args():
  parser = optparse.OptionParser()
  parser.add_option("--run_as_service", dest="run_as_service",
                    action="store_true", default=False,
                    help="Run the whitelist app as service")
  parser.add_option("--seed_whitelist_fname", dest="seed_whitelist_fname",
                    default="iso_whitelist.json",
                    help="The filename of the whitelist to load on launch")
  parser.add_option("--output_whitelist_fname", dest="output_whitelist_fname",
                    default="iso_whitelist.json",
                    help="The filename of the modifed whitelist")
  parser.add_option("--repo_root", dest="repo_root",
                    default="/home/brian/workspace/whitelist_repo/",
                    help="The top of the application's copy of the repo")
  parser.add_option("--unit_test_mode", dest="unit_test_mode",
                    action="store_true")
  return parser.parse_args()

if __name__ == "__main__":
  options, args = parse_args()
  if options.run_as_service:
    service(options, args)
  else:
    main(options, args)
