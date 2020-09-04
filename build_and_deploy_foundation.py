#!/bin/zsh
PWD=`pwd`;
cd $TOP;
make -j package-foundation;
cd $PWD;
PKG=`basename $TOP/build/foundation-*.tar.gz`;
scp $TOP/build/$PKG nutanix@$1:;
ssh nutanix@$1 foundation/bin/foundation_upgrade -t $PKG;
ssh nutanix@$1 rm $PKG;
