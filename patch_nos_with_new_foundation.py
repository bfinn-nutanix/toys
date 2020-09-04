#!/usr/bin/python -Bu

import json
import subprocess
import sys
import tarfile
import tempfile

nos_fname = sys.argv[1][:-3]
subprocess.check_call("gunzip %s" % sys.argv[1], shell=True)
foundation_fname = sys.argv[2]

def shell(*args):
  print("running command \"%s\"" % args[0])
  subprocess.check_call(*args, shell=True)

nos_tarball = tarfile.open(nos_fname, "r")
foundation_path = ""
metadata_path = ""
for path in nos_tarball.getnames():
  if "install/pkg/nutanix-foundation" in path:
    foundation_path = path
    print("found foundation path %s" % foundation_path)
  if "install/nutanix-packages.json" in path:
    metadata_path = path
    print("found metadata path %s" % metadata_path)
  if foundation_path and metadata_path:
    break
else:
  print("missing foundation or metadata file in NOS")
  sys.exit(1)

foundation_tarball = tarfile.open(foundation_fname)
for path in foundation_tarball.getnames():
  if "foundation/foundation_version" in path:
    version_fh = foundation_tarball.extractfile(path)
    break
else:
  print("missing version in foundation")
foundation_version = version_fh.read().strip()
foundation_version = "-".join(foundation_version.split("-")[1:])
print("found foundation version %s" % foundation_version)

metadata_fh = nos_tarball.extractfile(metadata_path)
metadata = json.load(metadata_fh)
foundation_metadata = {
  "depends" : [],
  "version" : foundation_version,
  "name"    : "nutanix-foundation",
  "reboot_required" : False
}
target_package_name = "install/pkg/nutanix-foundation-%s.tar.gz" % foundation_version
metadata["packages"] = [x for x in metadata["packages"] if
                              x["name"] != "nutanix-foundation"]
metadata["packages"].append(foundation_metadata)

shell("tar --delete -f %s %s" % (nos_fname, metadata_path))
with tempfile.NamedTemporaryFile() as new_metadata_fh:
  json.dump(metadata, new_metadata_fh, indent=4)
  new_metadata_fh.flush()
  shell("tar -r -f %s --xform s:.*:%s:g %s" % (nos_fname, metadata_path, new_metadata_fh.name))

shell("tar --delete -f %s %s" % (nos_fname, foundation_path))
shell("tar -r -f %s --xform s:.*:%s:g %s" % (nos_fname, target_package_name, foundation_fname))
shell("gzip %s" % (nos_fname))
