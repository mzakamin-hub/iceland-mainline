#!/bin/sh
# COPR "custom" source method script for package @PKG@ (made from packaging/copr/copr-custom-script.sh by
# copr-setup.sh). COPR runs it in an empty directory of a fedora-44-x86_64 chroot with network access; it writes the
# spec and every source file to ./result, from which COPR makes the source rpm and builds it on its aarch64 builders.
set -eu
git clone -q --depth 1 --branch main https://github.com/mzakamin-hub/iceland-mainline.git src
git -C src log -1 --format='iceland-mainline %H %s'
COPR_OWNER=@OWNER@ bash src/packaging/copr/make-srpm.sh @PKG@ --sources "$PWD/result"
