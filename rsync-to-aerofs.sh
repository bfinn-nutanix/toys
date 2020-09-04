#!/bin/bash
echo "Starting copy to AeroFS dir at " `date` >> /home/brian/AeroFS/rsync_log
rsync -av --delete /home/brian/main/infrastructure/theos /home/brian/AeroFS/
rsync -av --delete /home/brian/main/infrastructure/ashes /home/brian/AeroFS/
echo "Finished copy to AeroFS dir at " `date` >> /home/brian/AeroFS/rsync_log
