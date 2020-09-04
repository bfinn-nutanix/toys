#!/usr/bin/python

import subprocess
import time

def system(cmd, timeout=None):
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    shell=True)
  if timeout:
    deadline = time.time() + timeout
    while time.time() < deadline:
      ret = proc.poll()
      if ret is not None:
        break
    else:
      print("cmd %s timed out" % cmd)
      return None, None, None
  out, err = proc.communicate()
  return proc.returncode, out, err

def reboot_until_failure(ip):
  for attempt in range(100):
    print("attempt %s" % attempt)
    print("rebooting")
    system("sshpass -pnutanix/4u ssh root@%s reboot" % ip)
    time.sleep(300)
    print("waiting for the system to come back up")
    for retry in range(15):
      ret, out, err = system("sshpass -pnutanix/4u ssh root@%s cat "
        "/var/log/vmkernel.log" % ip)
      if ret == 0:
        print("system rebooted")
        time.sleep(60) # let it finish booting
        break
      time.sleep(60)
    else:
      print("timed out on attempt %s" % attempt)


if __name__ == "__main__":
  reboot_until_failure("10.5.50.58")
