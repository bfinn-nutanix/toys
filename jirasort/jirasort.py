#!/usr/bin/python2.7 -B

import getpass
import json
import requests
import sys
import time

from collections import deque

# Thanks SO
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

SERVER = "https://jira.nutanix.com"
UNAME = "bfinn"

def get_creds():
  connected = False
  while not connected:
    server = raw_input("JIRA server (%s): " % SERVER)
    if not server:
      server = SERVER
      print("Using server %s" % server)
    test = requests.get(server, verify=False)
    connected = test.status_code == 200
    if not connected:
      print("Couldn't connect to that server:\n\n%s\n\nPlease try again" %
        test.text)
  uname = raw_input("Username (%s): " % UNAME)
  if not uname:
    uname = UNAME
    print("Using username %s" % uname)
  pwd = getpass.getpass()
  test_with_auth = requests.get("%s/rest/api/2/issue/ENG-4" % server,
    auth=(uname, pwd), verify=False)
  if test_with_auth.status_code != 200:
    print(test_with_auth.text)
    return None
  else:
    return (server, uname, pwd)

def get_board(board_name, server, uname, pwd):
  board_cursor = requests.get("%s/rest/agile/1.0/board/?name=%s" %
    (server, board_name), auth=(uname, pwd), verify=False)
  board = board_cursor.json()
  return board["values"][0]["id"]

def get_board_configuration(board_id, server, uname, pwd):
  board_cursor = requests.get("%s/rest/agile/1.0/board/%d/configuration" %
    (server, board_id), auth=(uname, pwd), verify=False)
  board = board_cursor.json()
  return board["ranking"]["rankCustomFieldId"]

def get_backlog_issues(board_id, server, uname, pwd):
  start = time.time()
  print("Getting the backlog. Grab a cup of coffee.")
  received = 0
  done = False
  issues = []
  total = 1
  while received < total:
    board_cursor = requests.get(
      "%s/rest/agile/1.0/board/%d/backlog?startAt=%d" %
      (server, board_id, received), auth=(uname, pwd), verify=False)
    board = board_cursor.json()
    issues.extend(board["issues"])
    received += len(board["issues"])
    # Sketchy. Total may change. I would wait for len(board["issues"]) == 0
    # but JIRA docs suggest that may happen any time.
    total = board["total"]
  print("Backlog's in. Took %s seconds" % (time.time() - start))
  return issues

def merge(lists):
  """
  Given a list of lists, each sorted in priority order, merge to form a sorted
  list. Since I will do many comparisons, I sacrifice elegance of
  implementation to easily stopping and resuming manual work.
  """
  brk = False
  while len(lists) > 1:
    try:
      merged = merge_two(lists.popleft(), lists.popleft())
      lists.append(merged)
    except MergeAbortedError as e:
      # N.B. breaks the usual guarantee that elements of lists are ordered by
      # length, but that wll be restored after the next two rounds of
      # merge_two. It is not important that I solve this problem right now.
      for lst in (e.merged, e.l2, e.l1):
        if len(lst):
          lists.appendleft(lst)
      brk = True
    print("saving")
    with open("save", "w") as fh:
      json.dump(list(lists), fh, indent=2)
    if brk:
      print("bye!")
      break
  else:
    print("whoo!")

def merge_two(l1, l2):
  len_l1 = len(l1)
  len_l2 = len(l2)
  merged_size = len_l1 + len_l2
  result = [None] * merged_size
  i = 0
  j = 0
  while i + j < merged_size:
    try:
      if i < len_l1 and (j >= len_l2 or compare(l1[i], l2[j]) >=1):
        result[i+j] = l1[i]
        i += 1
      else:
        result[i+j] = l2[j]
        j += 1
    except StandardError as e:
      print(e)
      raise MergeAbortedError(l1[i:], l2[j:], result[0:i+j])
  return result

def compare(a, b):
  print("\n--------------------------")
  print("%s:\n%s\nSummary: %s\nDescription: %s" % (a["key"],
    a["fields"]["priority"]["name"], a["fields"]["summary"],
    a["fields"]["description"][0:256]))
  print("\n")
  print("%s:\n%s\nSummary: %s\nDescription: %s" % (b["key"],
    b["fields"]["priority"]["name"], b["fields"]["summary"],
    b["fields"]["description"][0:256]))
  choice = None
  while not choice in [1, 2]:
    print("\nPick the higher priority: 1 for %s; 2 for %s; or \"quit\" to "
      "save and resume later." % (a["key"], b["key"]))
    choice = raw_input("> ")
    if choice == "quit":
      confirmation = raw_input("you sure bro? y/n ")
      if confirmation == "y":
        raise StandardError("abort")
    else:
      try:
        choice = int(choice)
      except ValueError:
        print("Don't be smart. 1, 2, or quit. Jerk.")
  if choice == 1:
    return 1
  else:
    return -1

def rank_prompt(creds):
  # TODO: graceful prompt and nicer interaction
  while True:
    issue = raw_input("Issue to rank: ")
    direction = raw_input("Before/after: ")
    location = raw_input("Rank relative to issue: ")
    rank(creds, issue, direction, location)


def rank(creds, issue, direction, location):
  if direction not in ["before", "after"]:
    print("%s is not \"before\" or \"after\"" % direction)
    return
  server, uname, pwd = creds
  rank_url = "%s/rest/agile/1.0/issue/rank" % server
  data = {"issues": [issue]}
  if direction == "before":
    data["rankBeforeIssue"] = location
  elif direction == "after":
    data["rankAfterIssue"] = location

  r = requests.put(rank_url, headers = {"content-type": "application/json"},
    auth=(uname, pwd), verify=False, data=json.dumps(data))
  print r
  print r.text


class MergeAbortedError(Exception):
  def __init__(self, l1, l2, merged, *args, **kwargs):
    super(MergeAbortedError, self).__init__(*args, **kwargs)
    self.l1 = l1
    self.l2 = l2
    self.merged = merged

if __name__ == "__main__":
  usage = ("Usage: \"jirasort.py get_all_issues fname\", \"jirasort.py sort "
      "fname\", \"jirasort.py upload fname\", \"jirasort.py rank [x (before|"
      "after) y]\"")
  if len(sys.argv) < 2:
    print(usage)
    sys.exit(1)
  cmd = sys.argv[1]
  if cmd == "rank":
    creds = get_creds()
    if len(sys.argv) == 5 and sys.argv[3] in ["before", "after"]:
      rank(creds, sys.argv[2], sys.argv[3], sys.argv[4])
    else:
      rank_prompt(creds)
  if len(sys.argv < 3):
    print(usage)
    sys.exit(1)
  if cmd == "get_all_issues":
    server, uname, pwd = get_creds()
    board_id = get_board("Foundation", server, uname, pwd)
    issues = get_backlog_issues(board_id, server, uname, pwd)
    with open(sys.argv[2], "w") as fh:
      json.dump([[issue] for issue in issues], fh, indent=2)
  elif cmd == "sort":
    with open(sys.argv[2]) as fh:
      lists = deque(json.load(fh))
    merge(lists)
  else:
    print(usage)
    sys.exit(1)
