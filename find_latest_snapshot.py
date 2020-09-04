#!/usr/bin/python

import argparse
import glob
import os

def main(args):
  last_path = None
  instances_found = 0
  for path in sorted(os.listdir(args.snapshot_dir)):
    print("globbing %s" % os.path.join(args.snapshot_dir, path, args.path_glob))
    if glob.glob(os.path.join(args.snapshot_dir, path, args.path_glob)):
      instances_found += 1
      last_path = path

  if instances_found:
    print("Found %d instances, the last at %s" % (instances_found,
      os.path.join(args.snapshot_dir, last_path)))
  else:
    print("Didn't find your thing. Please check the snapshot path and glob.")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("path_glob")
  # TODO: in really old snapshots, there was no GoldImage directory - the
  # contents of GoldImage are in the snapshot root.
  parser.add_argument("--snapshot_dir", "-s",
    default="/net/filer/mnt/ZFS/GoldImages/.zfs/snapshot")
  args = parser.parse_args()
  main(args)
