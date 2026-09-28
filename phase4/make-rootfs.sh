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

# 1. the base: either Fedora's OCI image (index.json -> manifest -> layers, applied in order) or a rootfs tarball
#    captured from a previous RAM boot (the kit's 'rootfstar' page, e.g. after a dnf install)
case "$IMG" in
*.oci.tar.xz|*.oci.tar)
	tar -xf "$IMG" -C "$W/oci"
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
	done < "$W/layers" ;;
*.tar.gz|*.tgz|*.tar)
	echo "rootfs tarball $(basename "$IMG") ($(du -h "$IMG" | cut -f1))"
	fr tar -xf "$IMG" -C "$W/rootfs"
	fr mkdir -p "$W/rootfs/proc" "$W/rootfs/sys" "$W/rootfs/dev" "$W/rootfs/tmp" "$W/rootfs/run" ;;
*)	echo "unknown image type: $IMG"; exit 1 ;;
esac
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
# iceland: the Fedora rootfs's own init when the image has no systemd. Either PID 1 after switch_root, or
# (ROOTFS_MODE=chroot, the default of the kit's shim) a chroot beside the shim, which keeps the report pages and
# the live kmsg stream; then the pages are on 8080 and telnet on 2323. Every step is logged to the kernel log.
export PATH=/iceland/bbin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/root
HP=${ICELAND_HTTP_PORT:-80}; TP=${ICELAND_TELNET_PORT:-23}
[ -c /dev/kmsg ] || { mkdir -p /dev; mount -t devtmpfs dev /dev 2>/dev/null; }
exec > /dev/kmsg 2>&1
k() { echo "iceland-rootfs: $*"; }
k "init.sh started (pid $$, bash $BASH_VERSION, http $HP telnet $TP)"
/iceland/busybox --install -s /iceland/bbin && k "busybox applets in /iceland/bbin"
[ -d /proc/self ] || mount -t proc proc /proc; [ -d /sys/kernel ] || mount -t sysfs sys /sys
mkdir -p /dev/pts /run /tmp; mount -t devpts devpts /dev/pts 2>/dev/null
/iceland/busybox httpd -p "$HP" -h /iceland/www && k "report pages up on port $HP"
/iceland/busybox telnetd -p "$TP" -l /bin/bash && k "telnet root shell on port $TP"
k "$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | tr -d '"'): $(timeout 10 ldd --version 2>&1 | head -n1)"
k "dnf5: $(timeout 60 dnf5 --version 2>&1 | head -n1) (exit $?)"
k "rootfs: $(df -h / | tail -n1 | tr -s ' ') mem: $(free -m | awk '/^Mem:/{print $2" MiB, "$7" MiB available"}')"
if [ -s /iceland/proxy ]; then
	p=$(cat /iceland/proxy)
	k "proxy $p: http $(timeout 20 curl -s -m 15 -o /dev/null -w '%{http_code}' -x "$p" http://dl.fedoraproject.org/pub/fedora/linux/releases/ 2>&1), https $(timeout 20 curl -s -m 15 -o /dev/null -w '%{http_code}' -x "$p" https://dl.fedoraproject.org/pub/fedora/linux/releases/ 2>&1)"
	if [ -s /iceland/dnf-packages ]; then
		k "dnf5 install $(tr '\n' ' ' < /iceland/dnf-packages)"
		https_proxy=$p http_proxy=$p timeout 900 dnf5 -y --setopt=install_weak_deps=False install $(cat /iceland/dnf-packages) > /tmp/dnf.log 2>&1
		k "dnf5 exit $? : $(tail -n 3 /tmp/dnf.log | tr '\n' '|')"
	fi
fi
k "idle (telnet 172.16.42.1 $TP for a root shell)"
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
ExecStart=/iceland/busybox httpd -f -p 8080 -h /iceland/www
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
ExecStart=/iceland/busybox telnetd -F -p 2323 -l /bin/bash
Restart=always

[Install]
WantedBy=multi-user.target
EOF
# with systemd as PID 1 the dnf step runs as a oneshot unit (the same proxy/package files as init.sh)
cat > "$W/dnf.sh" <<'EOF'
#!/bin/bash
# iceland: dnf5 through the PC's proxy (/iceland/proxy, /iceland/dnf-packages), logged to the kernel log
k() { echo "iceland-rootfs: $*" > /dev/kmsg; }
[ -s /iceland/proxy ] || { k "dnf: no proxy configured"; exit 0; }
p=$(cat /iceland/proxy)
k "proxy $p: http $(timeout 20 curl -s -m 15 -o /dev/null -w '%{http_code}' -x "$p" http://dl.fedoraproject.org/pub/fedora/linux/releases/ 2>&1), https $(timeout 20 curl -s -m 15 -o /dev/null -w '%{http_code}' -x "$p" https://dl.fedoraproject.org/pub/fedora/linux/releases/ 2>&1)"
[ -s /iceland/dnf-packages ] || { k "dnf: nothing to install"; exit 0; }
k "dnf5 install $(tr '\n' ' ' < /iceland/dnf-packages)"
https_proxy=$p http_proxy=$p timeout 1200 dnf5 -y --setopt=install_weak_deps=False install $(cat /iceland/dnf-packages) > /tmp/dnf.log 2>&1
k "dnf5 exit $? : $(tail -n 3 /tmp/dnf.log | tr '\n' '|')"
# GPU check when kmscube was installed: a GBM/EGL spinning cube straight on the MSM DRM device (300 frames).
# kmscube exits after one frame ("user interrupted!") when its stdin is closed or at EOF, as under a unit or ssh
# (pc-024 Y8): feed it from a silent pipe so the "Rendered N frames" line appears. Lines kept short for /dev/kmsg.
if command -v kmscube >/dev/null; then
	card=$(ls /dev/dri/card* 2>/dev/null | tail -n1)
	sleep 90 | timeout 60 kmscube -D "$card" -c 300 > /tmp/kmscube.log 2>&1
	k "kmscube on $card exit $?: $(grep -iE 'renderer|rendered|interrupt|fail|error' /tmp/kmscube.log | cut -c1-120 | tail -n 3 | tr '\n' '|')"
	k "gpu: $(dmesg | grep -iE 'adreno|gmu|zap|freedreno' | grep -vE 'sync_state' | tail -n 3 | cut -c1-150 | tr '\n' '|')"
fi
# an optional test script carried by the kit (build.sh EXTRA_ETC rootfs-post.sh -> /iceland/post.sh, copied in by
# the shim at the hand-over): pc-024 Y9 runs the Wayland compositor test from it. Its log stays in /tmp/post.log.
if [ -x /iceland/post.sh ]; then
	k "post.sh: start at $(cut -d' ' -f1 /proc/uptime) s"
	/iceland/post.sh > /tmp/post.log 2>&1
	k "post.sh: exit $? at $(cut -d' ' -f1 /proc/uptime) s"
fi
EOF
fr install -m 0755 "$W/dnf.sh" "$R/iceland/dnf.sh"
cat > "$W/iceland-dnf.service" <<'EOF'
[Unit]
Description=iceland: dnf5 through the PC's proxy on the USB link
After=NetworkManager.service iceland-report.service

[Service]
Type=oneshot
ExecStart=/iceland/dnf.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
for u in iceland-report iceland-telnet iceland-dnf; do
	fr install -m 0644 "$W/$u.service" "$R/etc/systemd/system/$u.service"
	fr ln -sf "../$u.service" "$R/etc/systemd/system/multi-user.target.wants/$u.service"
done
# a serial console getty is useless here; keep the boot quiet on the panel: the report pages are the console
fr ln -sf /dev/null "$R/etc/systemd/system/getty@tty1.service"
# with systemd as PID 1 (an image where dnf installed it): NetworkManager keeps usb0 at the shim's address
# (the PC holds its DHCP lease for the session), sshd is enabled, and the PC's key logs in as root
if [ -d "$R/etc/NetworkManager" ]; then
	cat > "$W/usb0.nmconnection" <<'EOF'
[connection]
id=usb0
type=ethernet
interface-name=usb0
autoconnect=true

[ipv4]
method=manual
address1=172.16.42.1/24

[ipv6]
method=ignore
EOF
	fr install -m 0600 "$W/usb0.nmconnection" "$R/etc/NetworkManager/system-connections/usb0.nmconnection"
	fr ln -sf /usr/lib/systemd/system/NetworkManager.service "$R/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
fi
if [ -e "$R/usr/lib/systemd/system/sshd.service" ]; then
	fr ln -sf /usr/lib/systemd/system/sshd.service "$R/etc/systemd/system/multi-user.target.wants/sshd.service"
	printf 'PermitRootLogin prohibit-password\n' > "$W/iceland-sshd.conf"
	fr install -m 0600 "$W/iceland-sshd.conf" "$R/etc/ssh/sshd_config.d/10-iceland.conf"
fi
if [ -s "$HOME/.ssh/iceland.pub" ]; then
	fr mkdir -p -m 0700 "$R/root/.ssh"
	fr install -m 0600 "$HOME/.ssh/iceland.pub" "$R/root/.ssh/authorized_keys"
	echo "root ssh key: $(cut -d' ' -f3 "$HOME/.ssh/iceland.pub")"
fi

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
