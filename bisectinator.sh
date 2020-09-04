SPLIT=1
while [ $SPLIT -eq 1 ]; do
  make -j all_pydeps
  cd ~/workspace/main/infrastructure/phoenix/bootloader/initrd/phoenix
  GOOD=1
  TEST_OUTPUT=`make test`
  echo "$TEST_OUTPUT"
  echo "$TEST_OUTPUT" | grep -q "firmware_installer_test.py .......***Failed"
  if [ $? -eq 0 ]; then
    GOOD=0
  fi
  echo "Good: $GOOD"
  cd $TOP
  if [ $GOOD -eq  1 ]; then
    BISECT=`git bisect good`
  else
    BISECT=`git bisect bad`
  fi
  echo "$BISECT"
  echo "$BISECT" | grep -q "1 revision "
  SPLIT=$?
  echo "Split: $SPLIT"
done
