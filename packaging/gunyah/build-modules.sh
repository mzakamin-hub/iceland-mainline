#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# build-modules.sh - build the Gunyah VM-manager modules out of tree for one kernel-iceland kernel.
#
#   build-modules.sh --src LINUX [--rev COMMIT] --kout KBUILD [--kver KVER] [--out DIR]
#   build-modules.sh --src LINUX [--rev COMMIT] --config CONFIG --full [--kver KVER] [--out DIR]
#
#   --src LINUX     a git tree of iceland-linux (github.com/mzakamin-hub/iceland-linux), checked out at the exact
#                   commit the kernel was built from (kernel-iceland: /usr/lib/modules/<kver>/BUILD_INFO names it).
#                   It is not modified: the patches go into a temporary git worktree of that commit.
#   --rev COMMIT    the commit to build from instead of the tree's HEAD (e.g. 5baf75b61533 for q89n)
#   --kout KBUILD   the finished build directory of that kernel (the O= directory of `make Image modules`): the
#                   script takes its .config and Module.symvers. Fast (about a minute).
#   --config FILE   instead of --kout: only the kernel's config (e.g. /usr/lib/modules/<kver>/config of an installed
#   --full          kernel-iceland). The script then builds all modules once to get Module.symvers (slow: about
#                   15 min on a PC, much longer on the tablet). kernel-iceland ships no build directory
#                   (no kernel-iceland-devel), so an installed kernel alone is not enough for --kout.
#   --kver KVER     the kernel release the modules are for (default: KBUILD/include/config/kernel.release, or
#                   the version in the path of --config /usr/lib/modules/<kver>/config).
#   --out DIR       output directory (default ./out-<kver>)
#
# Result: DIR/gunyah/{mods/*.ko, gh_vmtest.py, gunyah-rehearsal.sh, SHA256SUMS} and DIR/gunyah-mods-<kver>.tar.gz
# (unpacks to gunyah/: `sudo tar -C /run -xzf ...` gives /run/gunyah, where gunyah-rehearsal.sh expects it).
# The modules are debug-stripped; their vermagic must equal the kernel's (checked).
#
# Toolchain: the kernel's own (kernel-iceland is built with LLVM=1; BUILD_INFO names the clang). On the PC:
# ARCH=arm64 with clang/lld on PATH; on the tablet (aarch64 Fedora): dnf install clang lld llvm make bc bison
# flex elfutils-libelf-devel openssl-devel git-core python3. Only toolchain lines of the config may change when
# the patches' config fragment (gunyah.config) is merged; anything else stops the build.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
src= rev=HEAD kout= config= full=0 kver= out=
while [ $# -gt 0 ]; do
	case "$1" in
	--src) src=$2; shift 2 ;;
	--rev) rev=$2; shift 2 ;;
	--kout) kout=$2; shift 2 ;;
	--config) config=$2; shift 2 ;;
	--full) full=1; shift ;;
	--kver) kver=$2; shift 2 ;;
	--out) out=$2; shift 2 ;;
	-h | --help) sed -n '3,31p' "$0"; exit 0 ;;
	*) echo "unknown argument: $1" >&2; exit 2 ;;
	esac
done
die() { echo "build-modules: $*" >&2; exit 1; }
[ -n "$src" ] && git -C "$src" rev-parse --git-dir > /dev/null 2>&1 || die "--src must be a git tree of iceland-linux"
src=$(cd "$src" && pwd)
if [ -n "$kout" ]; then
	kout=$(cd "$kout" && pwd)
	[ -f "$kout/.config" ] || die "$kout/.config missing"
	[ -f "$kout/Module.symvers" ] || die "$kout/Module.symvers missing (build the kernel's modules first, or use --config + --full)"
	config=$kout/.config
	[ -n "$kver" ] || kver=$(cat "$kout/include/config/kernel.release" 2>/dev/null || true)
elif [ -n "$config" ]; then
	[ "$full" = 1 ] || die "--config needs --full (no Module.symvers without a build)"
	[ -f "$config" ] || die "$config missing"
	config=$(cd "$(dirname "$config")" && pwd)/$(basename "$config")
	[ -n "$kver" ] || kver=$(echo "$config" | sed -n 's|.*/lib/modules/\([^/]*\)/config$|\1|p')
else
	die "give --kout KBUILD or --config FILE --full"
fi
[ -n "$kver" ] || die "kernel release unknown: give --kver"
out=${out:-$PWD/out-$kver}
mkdir -p "$out"; out=$(cd "$out" && pwd)

arch=()
[ "$(uname -m)" = aarch64 ] || arch=(ARCH=arm64)
command -v clang > /dev/null || die "clang not on PATH"
strip=$(command -v llvm-strip || true)
[ -n "$strip" ] || die "llvm-strip not on PATH"
jobs=$(nproc)

work=$(mktemp -d "${TMPDIR:-/tmp}/gunyah-build.XXXXXX")
wt=$work/linux
cleanup() { git -C "$src" worktree remove --force "$wt" > /dev/null 2>&1 || true; rm -rf "$work"; }
trap cleanup EXIT

echo "build-modules: kernel $kver, source $(git -C "$src" rev-parse --short=12 "$rev"), work $work"
git -C "$src" worktree add -q --detach "$wt" "$rev"
for p in "$here"/patches/*.patch; do
	git -C "$wt" apply --whitespace=nowarn "$p" || die "patch does not apply: $(basename "$p")"
done
echo "build-modules: applied $(ls "$here"/patches/*.patch | wc -l) patches"

o=$work/out
mkdir -p "$o"
cp "$config" "$o/.config"
cat "$here/gunyah.config" >> "$o/.config"
mk() { make -s -C "$wt" O="$o" "${arch[@]}" LLVM=1 KERNELRELEASE="$kver" -j"$jobs" "$@"; }
mk olddefconfig
norm() { grep '^CONFIG_' "$1" | grep -v '^CONFIG_GUNYAH' | sort; }
toolchain='^[<>] CONFIG_(CC_|AS_|LD_|CLANG_VERSION|LLD_VERSION|GCC_VERSION|RUSTC_|PAHOLE_VERSION|TOOLCHAIN_|TOOLS_SUPPORT_)'
delta=$(diff <(norm "$config") <(norm "$o/.config") | grep '^[<>]' | grep -vE "$toolchain" || true)
[ -z "$delta" ] || { echo "$delta"; die "merging gunyah.config changed other kernel options"; }
grep -q '^CONFIG_GUNYAH=m' "$o/.config" || die "CONFIG_GUNYAH=m did not stick (arm64 + GUNYAH dependencies?)"

if [ "$full" = 1 ]; then
	echo "build-modules: --full: building all modules for Module.symvers (slow)"
	mk modules
	m_hyp=$o/arch/arm64/gunyah m_virt=$o/drivers/virt/gunyah
else
	mk modules_prepare
	cp "$kout/Module.symvers" "$o/Module.symvers"
	m_hyp=$work/mod/hyp m_virt=$work/mod/virt
	mkdir -p "$m_hyp" "$m_virt"
	mk M="$wt/arch/arm64/gunyah" MO="$m_hyp" modules
	mk M="$wt/drivers/virt/gunyah" MO="$m_virt" KBUILD_EXTRA_SYMBOLS="$m_hyp/Module.symvers" modules
fi

pkg=$out/gunyah
rm -rf "$pkg"; mkdir -p "$pkg/mods"
for m in gunyah_hypercall timer; do cp "$m_hyp/$m.ko" "$pkg/mods/"; done
for m in gunyah gunyah_rsc_mgr gunyah_vcpu gunyah_platform_hooks gunyah_qcom gunyah_irqfd gunyah_ioeventfd gunyah_qtvm; do
	cp "$m_virt/$m.ko" "$pkg/mods/"
done
"$strip" --strip-debug "$pkg"/mods/*.ko
for k in "$pkg"/mods/*.ko; do
	vm=$(modinfo -F vermagic "$k" | cut -d' ' -f1)
	[ "$vm" = "$kver" ] || die "$(basename "$k"): vermagic $vm != $kver"
done
install -m 0755 "$here/gh_vmtest.py" "$here/gunyah-rehearsal.sh" "$pkg/"
(cd "$pkg" && sha256sum mods/*.ko gh_vmtest.py gunyah-rehearsal.sh > SHA256SUMS)
tar -C "$out" --owner=0 --group=0 -czf "$out/gunyah-mods-$kver.tar.gz" gunyah
echo "build-modules: $(ls "$pkg"/mods | wc -l) modules, vermagic $kver"
echo "build-modules: $out/gunyah-mods-$kver.tar.gz sha256 $(sha256sum < "$out/gunyah-mods-$kver.tar.gz" | cut -c1-64)"
