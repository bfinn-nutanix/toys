#!/usr/bin/python -B
import json
import requests
import sys

localhost = "http://localhost:8000/foundation"

with open(sys.argv[1]) as fh:
  params = json.loads(fh.read())

resp = requests.post("%s/image_nodes" % localhost,
                     headers={"content-type": "application/json"},
                     data=json.dumps(params, indent=2))

print resp
print resp.text
