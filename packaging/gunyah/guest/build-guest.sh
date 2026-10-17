#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# build-guest.sh SRC_GIT REV OUT - build the Gunyah test guest kernel: allnoconfig + guest.config, with a
# built-in initramfs holding a nolibc /init (init.c: one GUEST-HELLO line, then power-off). Result: OUT/Image
# (copy it to gunyah/guest/Image of the package) and OUT/.config. SRC_GIT is a Linux git tree (iceland-linux or
# any recent tree with tools/include/nolibc); REV is checked out in a worktree OUT/linux (its checkout stays as it is).
# Needs clang, lld and llvm-strip on PATH (LLVM=1, ARCH=arm64). BUILD_LOCK=FILE: hold FILE with flock -n.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); src=$1; rev=$2; out=$(mkdir -p "$3" && cd "$3" && pwd)
if [ -n "${BUILD_LOCK:-}" ]; then
	exec 9>"$BUILD_LOCK"; flock -n 9 || { echo "another build holds $BUILD_LOCK - refusing"; exit 1; }
fi
command -v clang > /dev/null && command -v ld.lld > /dev/null || { echo "clang / ld.lld not on PATH"; exit 1; }
wt=$out/linux; o=$out/kout
[ -d "$wt" ] || git -C "$src" worktree add -q --detach "$wt" "$rev"
mk() { nice -n 10 make -s -C "$wt" O="$o" ARCH=arm64 LLVM=1 -j"$(nproc)" "$@"; }
mkdir -p "$o"
mk headers_install INSTALL_HDR_PATH="$out/hdr"
clang --target=aarch64-linux-gnu -Os -static -nostdlib -ffreestanding -fno-stack-protector -fuse-ld=lld \
	-isystem "$out/hdr/include" -include "$wt/tools/include/nolibc/nolibc.h" -o "$out/init" "$here/init.c"
llvm-strip "$out/init"
printf 'dir /dev 0755 0 0\nnod /dev/console 0600 0 0 c 5 1\nnod /dev/kmsg 0600 0 0 c 1 11\nfile /init %s 0755 0 0\n' "$out/init" > "$o/initramfs.list"
mk allnoconfig
sed "s|\"initramfs.list\"|\"$o/initramfs.list\"|" "$here/guest.config" > "$o/guest.frag"
"$wt/scripts/kconfig/merge_config.sh" -m -O "$o" "$o/.config" "$o/guest.frag" > /dev/null
mk olddefconfig
for l in $(grep -E '^CONFIG_[A-Z0-9_]+=' "$o/guest.frag"); do
	k=${l%%=*}; v=${l#*=}
	if [ "$v" = n ]; then grep -q "^$k=" "$o/.config" && echo "WARN $k still set"; else grep -qx "$l" "$o/.config" || echo "WARN $l did not stick"; fi
done
mk Image
cp "$o/arch/arm64/boot/Image" "$o/.config" "$out/"
echo "guest Image $(stat -c %s "$out/Image") bytes, sha256 $(sha256sum < "$out/Image" | cut -c1-16)"
