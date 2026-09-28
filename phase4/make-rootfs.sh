#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Fedora aarch64 rootfs for a RAM boot on the OnePlus Pad 4 (Phase 4, nothing written to the tablet):
#   - unpack the official Fedora Container Base OCI image (it has systemd) under rootfs/;
#   - add the iceland pieces: the report pages (busybox httpd + the kit's CGI pages, restarted by a systemd unit
#     from /iceland), a telnet root shell on the USB link, our firmware, a stripped subset of our modules with
#     depmod, hostname;
#   - pack it as a cpio (paths rootfs/...) for tools/linux-ram/build.sh ROOTFS_CPIO. The kit's busybox init keeps
#     doing the early boot (USB network, live kmsg, module loading) and switch_roots into it at ROOTFS_AT.
# No root needed: fakeroot keeps ownership, modes and device nodes across the steps.
#   phase4/make-rootfs.sh OCI_TAR_XZ OUT_DIR MODSTAGE KVER FWDIR MODLIST BUSYBOX LINUX_RAM_DIR
set -euo pipefail
IMG=$1; OUT=$2; MS=$3; KVER=$4; FW=$5; ML=$6; BB=$7; LR=$8
W=$OUT/work; rm -rf "$W"; mkdir -p "$W/oci" "$W/rootfs"
S=$W/fakeroot.state; fakeroot -s "$S" true
fr() { fakeroot -i "$S" -s "$S" -- "$@"; }

# 1. the OCI image: index.json -> manifest -> layers, applied in order
tar -xJf "$IMG" -C "$W/oci"
python3 - "$W/oci" > "$W/layers" <<'EOF'
import json, sys
o = sys.argv[1]
idx = json.load(open(o + "/index.json"))
m = idx["manifests"][0]["digest"].split(":")[1]
man = json.load(open(o + "/blobs/sha256/" + m))
for l in man["layers"]:
    print(l["digest"].split(":")[1], l["mediaType"])
EOF
while read -r digest mtype; do
	echo "layer $digest ($mtype)"
	fr tar -xf "$W/oci/blobs/sha256/$digest" -C "$W/rootfs"
done < "$W/layers"
R=$W/rootfs
sed -n 's/^PRETTY_NAME=//p' "$R/etc/os-release"
if [ -x "$R/usr/lib/systemd/systemd" ]; then echo "systemd: yes"
else echo "systemd: no (the Container Base image has none: /iceland/init.sh runs as PID 1 instead)"; fi

# 2. iceland pieces
fr mkdir -p "$R/iceland/www/cgi-bin" "$R/iceland/bbin" "$R/etc/systemd/system/multi-user.target.wants"
fr install -m 0755 "$BB" "$R/iceland/busybox"
fr install -m 0755 "$LR/cgi-page" "$R/iceland/cgi-page"
fr install -m 0755 "$LR/cgi-reboot" "$R/iceland/cgi-reboot"
for p in $(sed -n 's|^slink /www/cgi-bin/\([a-z]*\) page .*|\1|p' "$LR/build.sh"); do
	fr ln -sf ../../cgi-page "$R/iceland/www/cgi-bin/$p"
done
fr ln -sf ../../cgi-reboot "$R/iceland/www/cgi-bin/reboot"
echo iceland | fr tee "$R/etc/hostname" > /dev/null
# PID 1 for an image without systemd: report pages + telnet shell, an optional dnf step through a proxy on the PC
# (/iceland/proxy holds its URL; /iceland/dnf-packages the package list), then idle. Everything stays in RAM.
cat > "$W/init.sh" <<'EOF'
#!/bin/bash
# iceland: PID 1 of the Fedora rootfs in RAM when the image has no systemd
k() { echo "iceland-rootfs: $*" > /dev/kmsg; }
export PATH=/iceland/bbin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/root
/iceland/busybox --install -s /iceland/bbin
mountpoint -q /proc || mount -t proc proc /proc; mountpoint -q /sys || mount -t sysfs sys /sys
mountpoint -q /dev || mount -t devtmpfs dev /dev; mkdir -p /dev/pts /run /tmp; mount -t devpts devpts /dev/pts 2>/dev/null
k "$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | tr -d '"') userland up as PID 1: bash $BASH_VERSION, $(ldd --version 2>/dev/null | head -n1), dnf5 $(dnf5 --version 2>/dev/null | head -n1)"
/iceland/busybox httpd -p 80 -h /iceland/www && k "report pages up"
/iceland/busybox telnetd -l /bin/bash && k "telnet shell up"
if [ -s /iceland/proxy ]; then
	p=$(cat /iceland/proxy); k "proxy $p: $(curl -s -m 10 -o /dev/null -w '%{http_code}' -x "$p" https://dl.fedoraproject.org/pub/fedora/linux/releases/ 2>&1 || echo unreachable)"
	if [ -s /iceland/dnf-packages ]; then
		k "dnf5 install $(tr '\n' ' ' < /iceland/dnf-packages)"
		https_proxy=$p http_proxy=$p dnf5 -y --setopt=install_weak_deps=False install $(cat /iceland/dnf-packages) > /tmp/dnf.log 2>&1
		k "dnf5 exit $? : $(tail -n 3 /tmp/dnf.log | tr '\n' '|')"
	fi
fi
k "idle (telnet 172.16.42.1 for a root shell)"
while :; do sleep 3600; done
EOF
fr install -m 0755 "$W/init.sh" "$R/iceland/init.sh"
cat > "$W/iceland-report.service" <<'EOF'
[Unit]
Description=iceland report pages (busybox httpd on the USB link)
After=local-fs.target

[Service]
Type=simple
Environment=PATH=/iceland/bbin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStartPre=/iceland/busybox --install -s /iceland/bbin
ExecStart=/iceland/busybox httpd -f -p 80 -h /iceland/www
Restart=always

[Install]
WantedBy=multi-user.target
EOF
cat > "$W/iceland-telnet.service" <<'EOF'
[Unit]
Description=iceland root shell over telnet on the USB link (debug kit only)
After=local-fs.target

[Service]
Type=simple
ExecStart=/iceland/busybox telnetd -F -l /bin/bash
Restart=always

[Install]
WantedBy=multi-user.target
EOF
for u in iceland-report iceland-telnet; do
	fr install -m 0644 "$W/$u.service" "$R/etc/systemd/system/$u.service"
	fr ln -sf "../$u.service" "$R/etc/systemd/system/multi-user.target.wants/$u.service"
done
# a serial console getty is useless here; keep the boot quiet on the panel: the report pages are the console
fr ln -sf /dev/null "$R/etc/systemd/system/getty@tty1.service"

# 3. firmware (proprietary, from the user's tablet: the image stays on the PC) and a stripped module subset
fr mkdir -p "$R/lib/firmware"
fr cp -a "$FW/." "$R/lib/firmware/"
MD=$R/lib/modules/$KVER; fr mkdir -p "$MD"
STRIP=$(command -v llvm-strip || ls "$HOME"/android/lineage/prebuilts/clang/host/linux-x86/clang-*/bin/llvm-strip | head -1)
n=0
for m in $(grep -v '^#' "$ML"); do
	modprobe -d "$MS" -S "$KVER" --show-depends "$m" 2>/dev/null | sed -n 's/^insmod //p' | while read -r ko; do
		rel=${ko#$MS/lib/modules/$KVER/}
		[ -e "$MD/$rel" ] && continue
		fr mkdir -p "$MD/$(dirname "$rel")"
		"$STRIP" --strip-debug -o "$W/ko.tmp" "$ko"; fr install -m 0644 "$W/ko.tmp" "$MD/$rel"
	done
	n=$((n + 1))
done
for f in modules.order modules.builtin modules.builtin.modinfo; do fr cp "$MS/lib/modules/$KVER/$f" "$MD/"; done
fr depmod -b "$R" "$KVER"
echo "modules: $(find "$MD" -name '*.ko' | wc -l) from $n names ($(du -sh "$MD" | cut -f1)); firmware $(du -sh "$R/lib/firmware" | cut -f1)"

# 4. pack (paths rootfs/...); the kernel unpacks it after the kit's own initramfs. Files the image ships with
# mode 000 (/etc/gshadow, /etc/shadow) are unreadable to the real user even under fakeroot: give them u+r first
# (they end up 0400 in the archive).
(cd "$W" && fr sh -c 'find rootfs -type f ! -perm -u+r -exec chmod u+r {} +')
(cd "$W" && fr sh -c 'find rootfs | cpio -o -H newc --quiet' | gzip -6 > "$OUT/rootfs.cpio.gz")
[ "${PIPESTATUS[0]:-0}" = 0 ] || { echo "cpio failed"; exit 1; }
rm -f "$W/ko.tmp"
{
	echo "image: $(basename "$IMG") sha256 $(sha256sum "$IMG" | cut -d' ' -f1)"
	echo "os: $(sed -n 's/^PRETTY_NAME=//p' "$R/etc/os-release")"
	echo "kernel-modules: $KVER"
	echo "date: $(date -u +%FT%TZ)"
} > "$OUT/rootfs.info"
ls -la "$OUT/rootfs.cpio.gz"; cat "$OUT/rootfs.info"
