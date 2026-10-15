# SPDX-License-Identifier: GPL-2.0-only
#
# kernel-iceland built FROM SOURCE (for COPR, packaging/copr): Linux (kernel.org tarball) + the iceland patch queue
# (github.com/mzakamin-hub/iceland-linux at one commit) + the kernel's full .config (config-iceland, beside this spec),
# compiled with Fedora's clang / lld (LLVM=1, as the PC builds use the Android clang of the same major version).
# The packaged files, scriptlets and dependencies are the same as the PC's repackaging spec (wf/ql/krpm-tool/
# kernel-iceland.spec, which wraps a finished PC build): /usr/lib/modules/<kver>/{vmlinuz,dtb/qcom/...,config,
# System.map,BUILD_INFO,modules}, depmod outputs as %ghost, kernel-install in %posttrans, installonlypkg(kernel).
# %prep PROVES the source: the base tarball's git tree = kernel.pin's UPSTREAM_TREE, the tree after each patch series =
# kernel.pin's TREE_AFTER_* (the same check the PC's mk-krpm scripts make). %build fails when `make olddefconfig`
# changes any option that is not a toolchain property (CC_*, AS_*, LD_*, *_VERSION ...).
# kernel.release = <base>-iceland-<number of queue patches>-q<queue commit, 12>: it sorts after the PC builds of the
# same queue (...-00438-g<hash>, rpm compares "q" > "g") and before the next queue (00439 ...).
#
# To move to a new queue: set queue_commit, npatches (0001 + 0002 patch files), base_tag / base_ver when the base
# changes, replace config-iceland by the new kernel's config (build/bin<tag>/config), add a changelog entry.

%global base_tag     7.3-rc7
%global base_ver     7.3.0-rc7
%global queue_commit aca0efd7d6b17e45132a81fe87608155618b8f87
%global queue_short  aca0efd7d6b1
%global npatches     00438
%global kver         %{base_ver}-iceland-%{npatches}-q%{queue_short}
%global kpkgver      %(echo %{kver} | sed 's/-rc/~rc/; s/-/./g')

%global debug_package %{nil}
%global __strip /bin/true
%global __os_install_post %{nil}
%global _build_id_links none

Name:           kernel-iceland
Version:        %{kpkgver}
Release:        1%{?dist}
Summary:        Linux kernel for the OnePlus Pad 4 (iceland, SM8850P)
License:        GPL-2.0-only
URL:            https://github.com/mzakamin-hub/iceland-linux
ExclusiveArch:  aarch64
Source0:        https://git.kernel.org/torvalds/t/linux-%{base_tag}.tar.gz
Source1:        https://github.com/mzakamin-hub/iceland-linux/archive/%{queue_commit}/iceland-linux-%{queue_commit}.tar.gz
Source2:        config-iceland
Source3:        90-iceland-dtb.install

BuildRequires:  make
BuildRequires:  clang
BuildRequires:  lld
BuildRequires:  llvm
BuildRequires:  bc
BuildRequires:  bison
BuildRequires:  flex
BuildRequires:  perl-interpreter
BuildRequires:  python3
BuildRequires:  openssl-devel
BuildRequires:  elfutils-libelf-devel
BuildRequires:  git-core
BuildRequires:  kmod
BuildRequires:  zstd
BuildRequires:  tar
BuildRequires:  gzip
BuildRequires:  findutils

Provides:       installonlypkg(kernel)
Provides:       kernel-iceland-uname-r = %{kpkgver}
# kernel-install runs the plug-ins: dracut (initramfs), grub2-tools (BLS entry, grub2-editenv), systemd-udev
Requires(posttrans): systemd-udev dracut grub2-tools kmod
Requires(preun): systemd-udev
Requires:       kmod
Recommends:     iceland-device

%description
Mainline Linux (%{kver}) with the OnePlus Pad 4 patch queue (iceland-linux %{queue_short}): kernel image, device
tree (qcom/kaanapali-oneplus-iceland.dtb), modules and config, built from source. kernel-install builds the
initramfs and the boot entry (/boot/loader/entries, with the per-kernel device tree when GRUB_DEVICETREE is set),
and keeps the device tree U-Boot loads from the EFI system partition in step with the confirmed kernel
(90-iceland-dtb.install). Source proof and toolchain: /usr/lib/modules/%{kver}/BUILD_INFO.

%prep
%setup -q -c -T -n kernel-iceland-%{kver}
tar -xzf %{SOURCE0}
tar -xzf %{SOURCE1}
Q=$PWD/iceland-linux-%{queue_commit}
[ -d linux-%{base_tag} ] && [ -f "$Q/kernel.pin" ] || { echo "source layout unexpected"; ls; exit 1; }
# the pin: UPSTREAM_TREE, TREE_AFTER_0001_infiniti, TREE_AFTER_0002_iceland (shell assignments)
eval "$(grep -E '^(UPSTREAM_TREE|TREE_AFTER_0001_infiniti|TREE_AFTER_0002_iceland)=[0-9a-f]{40}$' "$Q/kernel.pin")"
n1=$(ls "$Q"/patches/0001-infiniti/*.patch | wc -l); n2=$(ls "$Q"/patches/0002-iceland/*.patch | wc -l)
[ "$(printf %05d $((n1 + n2)))" = "%{npatches}" ] || { echo "queue has $n1 + $n2 patches, spec says %{npatches}"; exit 1; }
cd linux-%{base_tag}
git init -q --bare ../srcproof.git; git --git-dir=../srcproof.git config core.bare false
export GIT_DIR=$PWD/../srcproof.git GIT_WORK_TREE=$PWD
git add -A -f; t0=$(git write-tree)
[ "$t0" = "$UPSTREAM_TREE" ] || { echo "base tarball tree $t0 != kernel.pin UPSTREAM_TREE $UPSTREAM_TREE"; exit 1; }
for f in "$Q"/patches/0001-infiniti/*.patch; do git apply --index "$f" || { echo "does not apply: $f"; exit 1; }; done
t1=$(git write-tree); [ "$t1" = "$TREE_AFTER_0001_infiniti" ] || { echo "tree after 0001 $t1 != pin"; exit 1; }
for f in "$Q"/patches/0002-iceland/*.patch; do git apply --index "$f" || { echo "does not apply: $f"; exit 1; }; done
t2=$(git write-tree); [ "$t2" = "$TREE_AFTER_0002_iceland" ] || { echo "tree after 0002 $t2 != pin"; exit 1; }
unset GIT_DIR GIT_WORK_TREE; rm -rf ../srcproof.git
{
	echo "kernel-release: %{kver}"
	echo "base: linux-%{base_tag}.tar.gz sha256 $(sha256sum < %{SOURCE0} | cut -c1-64), git tree $t0 (= kernel.pin UPSTREAM_TREE)"
	echo "patch-queue-commit: %{queue_commit} (iceland-linux; $n1 + $n2 patches)"
	echo "tree-after-0001-infiniti: $t1 (= kernel.pin)"
	echo "tree-after-0002-iceland: $t2 (= kernel.pin)"
	echo "config-sha256: $(sha256sum < %{SOURCE2} | cut -c1-64) (config-iceland, before olddefconfig)"
} > ../BUILD_INFO
echo "source proof: base $t0, after 0001 $t1, after 0002 $t2 (all = kernel.pin)"

%build
cd linux-%{base_tag}
O=$PWD/../out; mkdir -p "$O"; cp %{SOURCE2} "$O/.config"
mk() { make -C "$PWD" O="$O" ARCH=arm64 LLVM=1 KBUILD_BUILD_USER=mzak KBUILD_BUILD_HOST=iceland-builder \
	LOCALVERSION=-%{npatches}-q%{queue_short} "$@"; }
mk -s olddefconfig
norm() { grep '^CONFIG_' "$1" | sort; }
diff <(norm %{SOURCE2}) <(norm "$O/.config") | grep '^[<>]' > ../config-delta.txt || :
grep -vE '^[<>] CONFIG_(CC_|AS_|LD_|CLANG_VERSION|LLD_VERSION|GCC_VERSION|RUSTC_|PAHOLE_VERSION|TOOLCHAIN_|TOOLS_SUPPORT_)' ../config-delta.txt > ../config-delta-other.txt || :
echo "config: $(wc -l < ../config-delta.txt) line(s) changed by olddefconfig, $(wc -l < ../config-delta-other.txt) not toolchain"
if [ -s ../config-delta-other.txt ]; then cat ../config-delta-other.txt; echo "STOP: olddefconfig changed kernel options"; exit 1; fi
mk -s include/config/kernel.release
[ "$(cat "$O/include/config/kernel.release")" = "%{kver}" ] || { echo "kernel.release $(cat "$O/include/config/kernel.release") != %{kver}"; exit 1; }
mk -j%{_smp_build_ncpus} Image modules qcom/kaanapali-oneplus-iceland.dtb
{
	echo "toolchain: $(clang --version | head -n1), $(ld.lld --version | head -n1)"
	echo "config-delta (olddefconfig, toolchain only): $(wc -l < ../config-delta.txt) lines"
} >> ../BUILD_INFO

%install
cd linux-%{base_tag}
O=$PWD/../out
m=%{buildroot}/usr/lib/modules/%{kver}
make -C "$PWD" O="$O" ARCH=arm64 LLVM=1 LOCALVERSION=-%{npatches}-q%{queue_short} INSTALL_MOD_PATH=%{buildroot}/usr \
	INSTALL_MOD_STRIP=1 DEPMOD=/bin/true -s modules_install
mkdir -p $m/dtb/qcom %{buildroot}/usr/lib/kernel/install.d
rm -f $m/build $m/source
install -m 0755 "$O/arch/arm64/boot/Image" $m/vmlinuz
install -m 0644 "$O/System.map" $m/System.map
install -m 0644 "$O/.config" $m/config
install -m 0644 "$O/arch/arm64/boot/dts/qcom/kaanapali-oneplus-iceland.dtb" $m/dtb/qcom/kaanapali-oneplus-iceland.dtb
{
	cat ../BUILD_INFO
	echo "image-sha256: $(sha256sum < "$O/arch/arm64/boot/Image" | cut -c1-64)"
	echo "dtb-sha256: $(sha256sum < "$O/arch/arm64/boot/dts/qcom/kaanapali-oneplus-iceland.dtb" | cut -c1-64)"
	echo "modules: $(find $m -name '*.ko*' | wc -l)"
	echo "packaged: built from source by kernel-iceland.spec (packaging/copr)"
} > $m/BUILD_INFO
install -m 0755 %{SOURCE3} %{buildroot}/usr/lib/kernel/install.d/90-iceland-dtb.install
# depmod's outputs are made on the system, not shipped (as Fedora's kernel does): listed as %ghost below
for f in alias alias.bin builtin.alias.bin builtin.bin dep dep.bin devname softdep symbols symbols.bin weakdep; do
	rm -f $m/modules.$f
done
# the same core checks as the PC's mk-krpm (wf/ql): the dtb, the in-tree camera sensor module, >= 900 modules
[ "$(find $m -name '*.ko*' | wc -l)" -ge 900 ] || { echo "fewer than 900 modules"; exit 1; }
find $m -name 'sc1320cs.ko*' | grep -q . || { echo "no sc1320cs module"; exit 1; }
grep -qa 'Linux version %{kver} (mzak@iceland-builder) ' "$O/arch/arm64/boot/Image" || { echo "Image version string"; exit 1; }

%posttrans
# the module index first (kernel-install's 50-depmod.install runs it too; dracut needs it)
depmod -a %{kver} || exit $?
/usr/bin/kernel-install add %{kver} /usr/lib/modules/%{kver}/vmlinuz || exit $?

%preun
/usr/bin/kernel-install remove %{kver} || :

%files
%dir /usr/lib/modules/%{kver}
/usr/lib/modules/%{kver}/*
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.alias
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.alias.bin
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.builtin.alias.bin
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.builtin.bin
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.dep
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.dep.bin
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.devname
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.softdep
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.symbols
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.symbols.bin
%ghost %attr(0644, root, root) /usr/lib/modules/%{kver}/modules.weakdep
/usr/lib/kernel/install.d/90-iceland-dtb.install

%changelog
* Fri Oct 16 2026 mzak <mzak.amin@gmail.com> - 7.3.0~rc7.iceland.00438.qaca0efd7d6b1-1
- First from-source spec (COPR): queue aca0efd (kernel q89l: q89k + 0319-0320) on v7.3-rc7, q89l's config;
  Fedora clang / lld; the source proven against kernel.pin in %%prep
