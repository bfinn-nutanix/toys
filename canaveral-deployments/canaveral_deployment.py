import certifi
import getpass
import json
import os
import requests
import sys
import time

TOKEN_FNAME = "CURRENT_TOKEN"

def get_token():
  if os.path.isfile(TOKEN_FNAME):
    try:
      with open(TOKEN_FNAME) as fh:
        token_file = fh.read()
        exp_time, token = token_file.splitlines()
        if time.time() < int(exp_time):
          return token
    except ValueError as e:
      # There's some garbage in the token file.
      print("Warning: there is garbage in token file %s. Trying to get a new "
        "token..." % TOKEN_FNAME)

  # TODO not sure it belongs here
  response = requests.get("http://canaveral-gatekeeper.canaveral-corp."
    "us-west-2.aws/ca/ca-chain.crt")
  with open(certifi.where(), "ab") as f:
      f.write(response.content)


  print "Username: ", # Python 2-ism: comma prevents trailing newline
  uname = sys.stdin.readline().strip()
  pwd = getpass.getpass()

  headers = {
    "Accept-Type": "application/json",
    "Content-Type": "application/json",
  }
  data = {
    "credential": {
      "type": "ldap",
      "mechanism": "user+pass",
      "payload": {
        "username": uname,
        "password": pwd,
        "realm": "corp.nutanix.com"
      }
    }
  }
  resp = requests.post(
    "https://canaveral-gatekeeper.canaveral-corp.us-west-2.aws/auth",
    headers=headers, data=json.dumps(data))
  if resp.status_code != 200:
    print("Couldn't get a token:\n%s" % resp.text)
  token = resp.json()["result"]

  with open(TOKEN_FNAME, "w") as fh:
    # TODO: if you already have a valid token, the service will return it. In
    # that case, I imagine the original expiration time still applies?
    fh.write("%s\n%s" % (int(time.time()) + 60*60, token))
  return token

def get_deployments(token, org, service, limit=0, offset=0):
  params = {"offset": offset}
  if limit:
    params["limit"] = limit
  resp = requests.get("https://canaveral-engine-api.canaveral-corp.us-west-2"
    ".aws/services/%s/%s/deployments" % (org, service), params=params,
    headers={"Authorization": "Bear %s" % token})
  if resp.status_code != 200:
    print("Couldn't get deployments:\n%s" % resp.text)
  else:
    print(json.dumps(resp.json(), indent=2))

def get_status(token, org, service, deployment):
  resp = requests.get("https://canaveral-engine-api.canaveral-corp.us-west-2"
    ".aws/services/%s/%s/deployments/%s" % (org, service, deployment),
    headers={"Authorization": "Bear %s" % token})
  if resp.status_code != 200:
    print("Couldn't get deployment:\n%s" % resp.text)
  else:
    print(json.dumps(resp.json(), indent=2))

def deploy_latest_config(token, org, service, package_id, pipeline):
  payload = {
    "package_id": package_id,
    "pipeline": pipeline,
  }
  headers = {
    "Authorization": "Bear %s" % token,
  }

  resp = requests.put("https://canaveral-engine-api.canaveral-corp.us-west-2"
    ".aws/services/%s/%s/deployments" % (org, service), json=payload,
    headers=headers)
  if resp.status_code != 200:
    print("Couldn't start deployment:\n%s" % resp.text)
  else:
    print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
  org = "xi-data-center-services"
  service = "bonxi-dns"
  deployment = "1561157301-8ac551"
  build_num = 57
  package_id = "/services/%s/%s/packages/%s/bonxi-dns.tar.gz" % (org, service,
    build_num)
  pipeline = "dev"
  token = get_token()
  #get_deployments(token, org, service, limit=1)
  #get_status(token, org, service, deployment)
  deploy_latest_config(token, org, service, package_id, pipeline)
