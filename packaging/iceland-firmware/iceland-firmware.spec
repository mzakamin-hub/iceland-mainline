# SPDX-License-Identifier: GPL-2.0-or-later
# iceland-firmware: the GENERIC firmware of the OnePlus Pad 4 (OPD2514, stock 11.A.38) at the paths the installer's
# extractor (iceland-fw-extract) writes today, so those files become package-owned with no gap: the package's files
# are byte-identical to the extracted ones (MANIFEST.tsv = the extraction's sha256), rpm replaces an unowned file
# with the same content in place, so nothing is ever absent. Unit-specific data (the sensor registry from persist,
# the Bluetooth address, the extraction record) is NOT in this package (EXCLUDED.tsv) and stays extractor-written.
# Firmware only: no scriptlets (no /bin/sh dependency), no services, no initramfs rebuild: 11.A.38-1 installs
# byte-identical copies, so the initramfs copies of gen80200_zap.mbn and novatek_nt36536_fw.bin (90-iceland-dracut.conf)
# stay valid. A later release that changes either file must add a posttrans scriptlet running
# "dracut -f --regenerate-all".
%global stock 11.A.38
# Hexagon / ARM ELF firmware in a noarch package: no strip, no build-id links, no debuginfo, no compression
%global _binaries_in_noarch_packages_terminate_build 0
%global _build_id_links none
%global debug_package %{nil}
%global __os_install_post %{nil}
%undefine _missing_build_ids_terminate_build

Name:           iceland-firmware
Version:        11.A.38
Release:        2%{?dist}
Summary:        Generic firmware of the OnePlus Pad 4 (Snapdragon 8 Elite Gen 5 / kaanapali)
License:        LicenseRef-Callaway-Redistributable-no-modification-permitted
URL:            https://github.com/mzakamin-hub/iceland-firmware
Source0:        iceland-firmware-%{version}.tar.gz
BuildArch:      noarch
# nothing to obsolete or conflict with: the first package of these paths; Fedora's linux-firmware ships no file
# under /usr/lib/firmware/updates (searched first by the kernel) and none under /usr/share/qcom/kaanapali/OnePlus
Provides:       iceland-firmware(stock) = %{stock}
# the sensor hub tree is root:fastrpc, dirs 0750 / files 0640: exactly what iceland-device's tmpfiles rule
# (iceland-dsp-tree.conf: Z /usr/share/qcom/kaanapali/OnePlus/iceland ~0750 root fastrpc) sets at every boot, so rpm -V
# stays clean (11.A.38-1 shipped root:root 0644 / 0755 -> 266 rpm -V lines on the 2nd boot, r143b); hexagonrpc's
# sysusers.d provides the group
Requires(pre):  group(fastrpc)

%description
The generic firmware every OnePlus Pad 4 runs in stock software 11.A.38: the ADSP / CDSP images, the GPU zap shader,
the video (VPU) firmware, the WCN7860 Wi-Fi and Bluetooth firmware and board files, the Novatek touch firmware, and the
sensor hub's file tree (DSP libraries, sensor configuration, audio calibration database). Installed under
/usr/lib/firmware/updates and /usr/share/qcom/kaanapali/OnePlus/iceland, where the mainline kernel, hexagonrpcd and
the iceland-device package expect them. MANIFEST.tsv lists each file's stock source and sha256.
Unit-specific data (sensor calibration registry, Bluetooth / Wi-Fi addresses) is not included.

%prep
%setup -q -n iceland-firmware-%{version}

%build
# nothing to build

%install
cp -a root/. %{buildroot}/
# the file list = exactly MANIFEST.tsv, plus every directory below /usr/lib/firmware and /usr/share that holds one of
# its files; the sensor registry directory (persist, private) is never listed
awk -F'\t' '!/^#/ && NF >= 2 { print $1 }' MANIFEST.tsv | sort > files.txt
: > %{name}.files
T=/usr/share/qcom/kaanapali/OnePlus/iceland
while read -r f; do case "$f" in "$T"/*) printf '%%%%attr(0640,root,fastrpc) "%%s"\n' "$f" ;; *) printf '"%%s"\n' "$f" ;; esac; done < files.txt >> %{name}.files
python3 - files.txt >> %{name}.files <<'PY'
import sys
dirs = set()
for f in open(sys.argv[1]).read().split():
    d = f.rsplit("/", 1)[0]
    while d not in ("/usr/lib/firmware", "/usr/share", ""):
        dirs.add(d)
        d = d.rsplit("/", 1)[0]
T = "/usr/share/qcom/kaanapali/OnePlus/iceland"
for d in sorted(dirs):
    a = "%%%%attr(0750,root,fastrpc) " if d == T or d.startswith(T + "/") else ""
    print("%%%%dir " + a + "\"" + d + "\"")
PY

%check
# every packaged file = the manifest's sha256 (the extraction), every manifest line packaged, nothing else
cd %{buildroot}
awk -F'\t' '!/^#/ && NF >= 2 { print $2 "  ." $1 }' %{_builddir}/iceland-firmware-%{version}/MANIFEST.tsv | sha256sum --quiet -c -
test "$(find . -type f | wc -l)" = "$(grep -c -v '^#' %{_builddir}/iceland-firmware-%{version}/MANIFEST.tsv)"
test ! -e ./usr/share/qcom/kaanapali/OnePlus/iceland/sensors/registry

%files -f %{name}.files
%license NOTICE.md Notice-qca-atheros.txt
%doc README.md MANIFEST.tsv EXCLUDED.tsv

%changelog
* Mon Oct 12 2026 mzak <mzak.amin@gmail.com> - 11.A.38-2
- The sensor hub tree as iceland-device's tmpfiles rule keeps it (root:fastrpc, dirs 0750, files 0640): rpm -V clean
  after a reboot (r143b: 266 mode / group lines with -1). Requires(pre) group(fastrpc). Content unchanged.

* Mon Oct 12 2026 mzak <mzak.amin@gmail.com> - 11.A.38-1
- First package: the generic files the installer extracted from stock 11.A.38 (sha256 = the extraction); the
  sensor registry (calibration), the Bluetooth address and the extraction record stay unit-specific and unpackaged.
