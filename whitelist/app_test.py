#!/usr/bin/python -Bu
#
# Copyright (c) 2016 Nutanix Inc. All rights reserved.
#
# Author: bfinn@nutanix.com
#
# Unit test for whitelist app
#

import json
import requests
import threading
import time
import unittest
import whitelist_app

ENTRIES = "http://localhost:9000/api/entries"
FILES = "http://localhost:9000/api/file"
TEST_JSON_FILE = "iso_whitelist.json.test"



class APITest(unittest.TestCase):
  def __init__(self, *args, **kwargs):
    super(APITest, self).__init__(*args, **kwargs)
    with open("iso_whitelist.json.sample") as fh:
      self.sample_whitelist = json.load(fh)["iso_whitelist"]

  def test_service_up(self):
    pass

  def test_get_all_checksums(self):
    default_keys = self.sample_whitelist.keys()
    resp = requests.get(ENTRIES)
    for checksum in default_keys:
      self.assertTrue(checksum in resp.json(), "Checksum list %s did not "
      "contain expected checksum %s" % (resp.json(), checksum))

  def test_get_entry(self):
    for checksum, entry in self.sample_whitelist.iteritems():
      resp = requests.get(ENTRIES, params={"checksum": checksum})
      if resp.status_code == 200:
        self.assertEqual(entry, resp.json(), "Entry for %s did not match "
          "expected entry %s" % (resp.json(), entry))
      else:
        self.fail("Got status code %s instead of 200 for checksum %s" %
          (resp.status_code, checksum))

  def test_get_bad_checksum(self):
    default_keys = self.sample_whitelist.keys()
    resp = requests.get(ENTRIES, params={"checksum": "bogus"})
    self.assertEqual(resp.status_code, 404, "Requesting a bogus installer "
      "returned %s instead of 404. Response body:\n%s" % (resp.status_code,
      resp.text))

  def test_create_entry(self):
    checksum = "000000"
    entry = {
      "min_foundation": "3.4",
      "hypervisor": "kvm",
      "min_nos": "4.7.2",
      "friendly_name": "the new version",
      "compatible_versions": {
        "kvm": [
          "^el6\\.nutanix\\.20160601.9999"
        ]
      },
      "version": "20160601.9999",
      "deprecated": None,
      "unsupported_hardware": []
    }
    post = requests.post(ENTRIES, params={"checksum": checksum},
      headers={"content-type": "application/json"}, data=json.dumps(entry))
    self.assertEqual(post.status_code, 200, "Posting new entry failed with %s"
      % post.text)

    get = requests.get(ENTRIES, params={"checksum": checksum})
    if get.status_code == 200:
      self.assertEqual(get.json(), entry, "The new entry %s didn't match "
        "input data %s" % (get.json(), entry))
    else:
      self.fail("Get gave response code %s instead of 200. Response text:\n%s"
        % (get.status_code, get.text))

    with open(TEST_JSON_FILE) as fh:
      test_json = json.load(fh)
    self.assertTrue(checksum in test_json["iso_whitelist"], "New entry was "
      "not added to the backing file.")
    new_entry = test_json["iso_whitelist"][checksum]
    self.assertEqual(entry, new_entry, "The new entry in the backing file\n"
      "%s\ndoesn't match the expected value:\n%s" % (new_entry, entry))

  def test_create_duplicate_entry(self):
    checksum, entry = self.sample_whitelist.items()[0]
    post = requests.post(ENTRIES, params={"checksum": checksum},
      headers={"content-type": "application/json"}, data=json.dumps(entry))
    self.assertEqual(post.status_code, 400, "Posting a duplicate entry "
      "returned %s rather than 400. Response text:\n%s" % (post.status_code,
      post.text))

  def test_update_entry(self):
    checksum = "000001"
    entry = {
      "min_foundation": "3.4",
      "hypervisor": "kvm",
      "min_nos": "4.7.2",
      "friendly_name": "the new version",
      "compatible_versions": {
        "kvm": [
          "^el6\\.nutanix\\.20160601.9999"
        ]
      },
      "version": "20160601.9999",
      "deprecated": None,
      "unsupported_hardware": []
    }
    post = requests.post(ENTRIES, params={"checksum": checksum},
      headers={"content-type": "application/json"}, data=json.dumps(entry))
    self.assertEqual(post.status_code, 200, "Posting new entry failed with %s"
      % post.text)

    # Oops!
    entry["deprecated"] = "3.5"
    put = requests.put(ENTRIES, params={"checksum": checksum},
      headers={"content-type": "application/json"}, data=json.dumps(entry))
    self.assertEqual(post.status_code, 200, "Updating new entry failed with "
      "%s and response text %s" % (post.status_code, post.text))

    get = requests.get(ENTRIES, params={"checksum": checksum})
    if get.status_code == 200:
      self.assertEqual(get.json()["deprecated"], "3.5", "The update did not "
        "stick. The entry contained deprecated value %s rather than the "
        "intended value 3.5" % get.json()["deprecated"])
    else:
      self.fail("Get gave response code %s instead of 200. Response text:\n%s"
        % (get.status_code, get.text))

    with open(TEST_JSON_FILE) as fh:
      test_json = json.load(fh)
    self.assertTrue(checksum in test_json["iso_whitelist"], "New entry was "
      "not added to the backing file.")
    new_entry = test_json["iso_whitelist"][checksum]
    self.assertEqual(entry, new_entry, "The new entry in the backing file\n"
      "%s\ndoesn't match the expected value:\n%s" % (new_entry, entry))

  def test_update_nonexistent_entry(self):
    entry = self.sample_whitelist.values()[0]
    put = requests.put(ENTRIES, params={"checksum": "bogus"},
      headers={"content-type": "application/json"}, data=json.dumps(entry))
    self.assertEqual(put.status_code, 404, "Updating a nonexistent entry "
      "returned %s rather than 404. Response text:\n%s" % (put.status_code,
      put.text))

  def test_delete_entry(self):
    checksum = "000002"
    entry = {
      "min_foundation": "3.4",
      "hypervisor": "kvm",
      "min_nos": "4.7.2",
      "friendly_name": "the new version",
      "compatible_versions": {
        "kvm": [
          "^el6\\.nutanix\\.20160601.9999"
        ]
      },
      "version": "20160601.9999",
      "deprecated": None,
      "unsupported_hardware": []
    }
    post = requests.post(ENTRIES, params={"checksum": checksum},
      headers={"content-type": "application/json"}, data=json.dumps(entry))
    self.assertEqual(post.status_code, 200, "Posting new entry failed with %s"
      % post.text)

    get = requests.get(ENTRIES, params={"checksum": checksum})
    if get.status_code == 200:
      self.assertEqual(get.json(), entry, "Posting the new entry didn't "
        "stick. Got entry %s instead of expected %s" % (get.json(), entry))
    else:
      self.fail("Get gave response code %s instead of 200. Response text:\n%s"
        % (get.status_code, get.text))

    delete = requests.delete(ENTRIES, params={"checksum": checksum})
    self.assertEqual(delete.status_code, 200, "Deleting the new entry failed "
      "with %s and response %s" % (delete.status_code, delete.text))

    get = requests.get(ENTRIES, params={"checksum": checksum})
    self.assertEqual(get.status_code, 404, "Get should have failed with 404 "
      "after deletion, but instead returned %s and text %s" % (
      get.status_code, get.text))

    with open(TEST_JSON_FILE) as fh:
      test_json = json.load(fh)
    self.assertFalse(checksum in test_json["iso_whitelist"], "Deleted entry "
      "still exists in the backing file")

  def test_delete_nonexistent_entry(self):
    delete = requests.delete(ENTRIES, params={"checksum": "bogus"})
    self.assertEqual(delete.status_code, 404, "Updating a nonexistent entry "
      "returned %s rather than 404. Response text:\n%s" % (delete.status_code,
      delete.text))

  def test_get_full_whitelist(self):
    get = requests.get(FILES + "/get_whitelist_as_file")
    self.assertEqual(get.status_code, 200, "Getting the whitelist failed "
      "with status %s and text %s" % (get.status_code, get.text))
    try:
      retrieved_whitelist = json.loads(get.text)
    except Exception as e:
      self.fail("Returned invalid json\n%s\nException message:\n%s" % (
        get.text, e))

    self.assertTrue("last_modified" in retrieved_whitelist, "Whitelist is "
      "missing its timestamp:\n%s" % (retrieved_whitelist))
    current_time = time.time()
    self.assertTrue(
      abs(current_time - retrieved_whitelist["last_modified"]) < 10,
      "Whitelist timestamp %s should have been close to current time %s" % (
      retrieved_whitelist["last_modified"], current_time))

    self.assertTrue("iso_whitelist" in retrieved_whitelist, "Whitelist is "
      "missing the crucial \"iso_whitelist\" attribute:\n%s" % (
      retrieved_whitelist))
    retrieved_entries = retrieved_whitelist["iso_whitelist"]
    for checksum, entry in self.sample_whitelist.iteritems():
      self.assertTrue(checksum in retrieved_entries, "Whitelist\n%s\ndid not "
        "contain expected checksum %s" % (retrieved_entries, checksum))
      self.assertEqual(entry, retrieved_entries[checksum], "Entry for "
        "checksum %s was %s rather than expected %s" % (checksum,
          retrieved_entries[checksum], entry))

  def test_get_validated_whitelist(self):
    get = requests.get(FILES + "/get_whitelist_as_file",
      params={"only_validated": True})
    self.assertEqual(get.status_code, 200, "Getting the whitelist failed "
      "with status %s and text %s" % (get.status_code, get.text))
    try:
      retrieved_whitelist = json.loads(get.text)
    except Exception as e:
      self.fail("Returned invalid json\n%s\nException message:\n%s" % (
        get.text, e))

    self.assertTrue("last_modified" in retrieved_whitelist, "Whitelist is "
      "missing its timestamp:\n%s" % (retrieved_whitelist))
    current_time = time.time()
    self.assertTrue(
      abs(current_time - retrieved_whitelist["last_modified"]) < 10,
      "Whitelist timestamp %s should have been close to current time %s" % (
      retrieved_whitelist["last_modified"], current_time))

    self.assertTrue("iso_whitelist" in retrieved_whitelist, "Whitelist is "
      "missing the crucial \"iso_whitelist\" attribute:\n%s" % (
      retrieved_whitelist))
    retrieved_entries = retrieved_whitelist["iso_whitelist"]
    for checksum, entry in self.sample_whitelist.iteritems():
      if entry["validated"]:
        self.assertTrue(checksum in retrieved_entries, "Whitelist\n%s\ndid "
          "not contain expected checksum %s" % (retrieved_entries, checksum))
        self.assertEqual(entry, retrieved_entries[checksum], "Entry for "
          "checksum %s was %s rather than expected %s" % (checksum,
            retrieved_entries[checksum], entry))
      else:
        self.assertFalse(checksum in retrieved_entries, "Whitelist\n%s\n"
          "contained un-validated checksum %s" % (retrieved_entries,
          checksum))

  # BIG TODO: automate testing the push.

if __name__ == "__main__":
  # Sure do wish python 2.6 had setUpClass :/
  opts, args = whitelist_app.parse_args()
  opts.seed_whitelist_fname = "iso_whitelist.json.sample"
  opts.output_whitelist_fname = TEST_JSON_FILE
  opts.unit_test_mode = True
  server = threading.Thread(target=whitelist_app.main,
    args=(opts, args))
  server.daemon = True
  server.start()

  # The server does a checkout and pull; this may take a while.
  time.sleep(5)
  server_up = False
  while not server_up:
    time.sleep(0.1)
    resp = requests.get("http://localhost:9000/alive")
    server_up = resp.status_code == 200
  unittest.main()
  server.stop()
