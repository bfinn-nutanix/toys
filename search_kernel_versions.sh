#!/usr/bin/zsh

FOUND=0
while [[ $FOUND -eq 0 ]]; do
BLAME="$(git blame Makefile.toolchain| grep "TOOLCHAIN_GIT_HASH =")"
HASH="${BLAME##* }"
KERNEL="$(file ~/workspace/toolchain_builds/$HASH.x86_64/kernels/phoenix/boot/bzImage)"
  if [[ -n "$(echo $KERNEL | grep 4.10.1)" ]]; then
    echo "$HASH: still 4.10.1"
    git checkout "${BLAME%% *}~"
  else
    FOUND=1
    echo "finally a change at $HASH: $KERNEL"
  fi
done
