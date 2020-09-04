#!/usr/bin/python

import subprocess
import argparse

HOSTS = ["fv-%d" % x for x in range(1,5)] + \
    ["symphony01-%d" % x for x in range(1,5)]

def main(args):
  print("-----")
  for host in HOSTS:
    proc = subprocess.Popen("sshpass -pnutanix/4u ssh root@%s uname -a" % host,
      stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    ret = proc.returncode
    #print("debug: ret %d out %s err %s" % (ret, out, err))
    if (args.host_type == "esx" and "VMkernel" in out) or \
      (args.host_type == "ahv" and "nutanix" in out):
       print("host %s: %s" % (host, out))
  print("-----")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("host_type", choices=["esx", "ahv"])
  args = parser.parse_args()
  main(args)
