#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# image/kiwi/tools/image-check.sh - the finished PC-built disk against the B150g invariants and B149's content. READ ONLY:
# a read-only loop per partition of the golden body (losetup -r -o / --sizelimit), every mount -o ro (ext4 noload, btrfs
# rescue=nologreplay). Needs root (WSL: wsl.exe -u root; CI: the privileged build container) and rpm, btrfs-progs, mtools.
#   image-check.sh GOLDEN.json OUT_DIR [B149.json]
# Writes OUT_DIR/{image-check.txt,manifest.tsv,manifest-diff.txt,esp-files.txt,lsinitrd.txt}. Last line of image-check.txt
# "IMAGE-CHECK: PASS|FAIL (n FAIL)". Rows:
#   gen_check (the B150g recipe's own list, sourced from recipe-src/gen-functions.sh: no unit data, wizard, provisioning,
#   growth, versions of ours, firmware ownership) | layout (types, names, 3 top-level subvolumes, fstab) | boot (entry:
#   $iceland_args, devicetree, root=UUID of p3; GRUB_DEVICETREE; ESP: shim + GRUB + the stub grub.cfg + the U-Boot DT copy)
#   | initramfs (iceland-carrier, nbd, the storage rule, zap, early dsp, root-firmware drivers left out) | manifest vs B149
set -u
J=${1:?GOLDEN.json}; OUT=${2:?OUT_DIR}; REF=${3:-}
HERE=$(cd "$(dirname "$0")" && pwd)
GENF=${GEN_FUNCS:-$HOME/mainline/build/wf/generic/recipe-src/gen-functions.sh}
[ -f "$GENF" ] || GENF=$HERE/gen-functions.sh
OURS=${OURS_TSV:-$HERE/../desc/ours.tsv}
mkdir -p "$OUT"; R=$OUT/image-check.txt; : > "$R"
nf=0
row() { echo "$1 $2" >> "$R"; [ "$1" = FAIL ] && nf=$((nf + 1)); return 0; }
[ "$(id -u)" = 0 ] || { echo "image-check: needs root (read-only loop mounts)"; exit 2; }
BODY=$(dirname "$J")/$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["body"])' "$J")
MNT=$(mktemp -d /tmp/iceland-check.XXXX); LOOPS=""
cleanup() { umount -R "$MNT" 2>/dev/null; for l in $LOOPS; do losetup -d "$l"; done; rmdir "$MNT" 2>/dev/null; }
trap cleanup EXIT
# one read-only loop per partition (offset and size from the golden json); no partition scan: the body ends at the root
# partition (its backup GPT is in the .tail), so the kernel would not take the GPT of a loop over the body alone
P1=; P2=; P3=
while read -r n off size; do
	l=$(losetup -r -f --show -o "$off" --sizelimit "$size" "$BODY") || { echo "image-check: losetup p$n failed"; exit 2; }
	LOOPS="$LOOPS $l"; eval "P$n=$l"
done < <(python3 -I -c 'import json,sys; [print(p["n"], p["offset"], p["bytes"]) for p in json.load(open(sys.argv[1]))["partitions"]]' "$J")
for p in "$P1" "$P2" "$P3"; do [ -b "$p" ] || { echo "image-check: a partition loop is missing ($P1 $P2 $P3)"; exit 2; }; done
# ---- layout
t=$(blkid -o value -s TYPE "$P1")/$(blkid -o value -s TYPE "$P2")/$(blkid -o value -s TYPE "$P3")
[ "$t" = vfat/ext4/btrfs ] && row PASS "layout: file systems $t" || row FAIL "layout: file systems $t (want vfat/ext4/btrfs)"
pt=$(python3 -I -c 'import json,sys; m=json.load(open(sys.argv[1])); print(" ".join(p["type"][:8]+"/"+p["name"].replace(" ","_") for p in m["partitions"]))' "$J")
[ "$pt" = "c12a7328/EFI_System_Partition bc13c2ff/boot b921b045/root" ] && row PASS "layout: GPT types + names as B149" || row FAIL "layout: GPT $pt"
mount -o ro,subvolid=5,rescue=nologreplay "$P3" "$MNT" || { echo "image-check: mount top level failed"; exit 2; }
sv=$(btrfs subvolume list -t "$MNT" 2>/dev/null | awk 'NR > 2 {print $3 ":" $NF}' | sort | tr '\n' ' ')
case "$sv" in "5:home 5:root 5:var ") row PASS "layout: btrfs top-level subvolumes root home var" ;; *) row FAIL "layout: btrfs subvolumes '$sv' (want root home var under 5)" ;; esac
umount "$MNT"
mount -o ro,subvol=root,rescue=nologreplay "$P3" "$MNT" && mount -o ro,subvol=var,rescue=nologreplay "$P3" "$MNT/var" \
	&& mount -o ro,subvol=home,rescue=nologreplay "$P3" "$MNT/home" && mount -o ro,noload "$P2" "$MNT/boot" \
	&& mount -o ro "$P1" "$MNT/boot/efi" || { echo "image-check: mounting the image failed"; exit 2; }
for m in / /home /var; do
	awk -v m="$m" '$2 == m && $3 == "btrfs" && $4 ~ /subvol=/ && $4 ~ /compress=zstd:1/' "$MNT/etc/fstab" | grep -q . && row PASS "fstab: $m btrfs subvol + zstd:1" || row FAIL "fstab: $m line"
done
for m in /boot /boot/efi; do awk -v m="$m" '$2 == m' "$MNT/etc/fstab" | grep -q '^UUID=' && row PASS "fstab: $m by UUID" || row FAIL "fstab: $m line"; done
# ---- gen_check, the B150g recipe's own invariants (the same function, the same expected versions)
export GEN_DEVREL=${GEN_DEVREL:-$(awk -F'\t' '$1 == "iceland-device" {print $2}' "$OURS")}
export GEN_IIO=${GEN_IIO:-$(awk -F'\t' '$1 == "iio-sensor-proxy" {print $2}' "$OURS")}
export GEN_FW=${GEN_FW:-$(awk -F'\t' '$1 == "iceland-firmware" {print $2}' "$OURS")}
export GEN_KREL=${GEN_KREL:-$(awk -F'\t' '$1 == "kernel-iceland" {print $2}' "$OURS")}
# shellcheck source=/dev/null
. "$GENF"
gc=$(gen_check); case "$gc" in "PASS "*) row PASS "gen_check: $gc" ;; *) row FAIL "gen_check: $gc" ;; esac
[ -e "$MNT/etc/iceland/generic-image" ] && row PASS "growth: marker /etc/iceland/generic-image" || row FAIL "growth: no /etc/iceland/generic-image (iceland-grow would do nothing)"
# ---- boot
KV=$(find "$MNT/usr/lib/modules" -mindepth 1 -maxdepth 1 -name '*-iceland*' -printf '%f\n' | sort -V | tail -n 1)
e=$(ls "$MNT"/boot/loader/entries/*-"$KV".conf 2>/dev/null | head -n 1)
ru=$(blkid -o value -s UUID "$P3")
if [ -n "$e" ]; then
	# kiwi writes its own order (the description's command line, then root= and rootflags=): every part once, $iceland_args last
	o=$(grep '^options ' "$e")
	if grep -q " root=UUID=$ru\( \|$\)" <<< "$o" && [ "$(grep -o 'rootflags=subvol=root\b' <<< "$o" | wc -l)" = 1 ] && grep -q '\$iceland_args$' <<< "$o"; then
		row PASS "boot: entry options root=UUID(p3), rootflags=subvol=root once, \$iceland_args last"
	else row FAIL "boot: entry options: $(sed "s/$ru/<p3>/" <<< "$o")"; fi
	# the managed options as the image's own iceland-cmdline computes them (its boot.conf, its firmware), before $iceland_args
	T=$(mktemp -d); mkdir -p "$T/etc/kernel" "$T/etc/iceland" "$T/usr/lib/firmware"
	cp "$MNT/etc/iceland/boot.conf" "$T/etc/iceland/" 2>/dev/null
	[ -d "$MNT/usr/lib/firmware/iceland-gpu-stock" ] && ln -s "$MNT/usr/lib/firmware/iceland-gpu-stock" "$T/usr/lib/firmware/iceland-gpu-stock"
	echo 'ICELAND_MARK $iceland_args' > "$T/etc/kernel/cmdline"
	ICELAND_ROOT=$T sh "$MNT/usr/libexec/iceland/iceland-cmdline" 2>/dev/null
	mo=$(sed -e 's/^ICELAND_MARK *//' -e 's/ *\$iceland_args$//' "$T/etc/kernel/cmdline"); rm -rf "$T"
	miss=""; for w in $mo; do grep -q " $w \$iceland_args\| $w .*\$iceland_args" <<< "$o" || miss="$miss $w"; done
	if [ -n "$mo" ] && [ -z "$miss" ]; then row PASS "boot: managed options before \$iceland_args: $mo"
	else row FAIL "boot: managed options '${mo:-none computed}', missing:${miss:- none}"; fi
	case " $mo " in *" firmware_class.path=/usr/lib/firmware/iceland-gpu-stock "*) row PASS "boot: stock GPU firmware selected (firmware_class.path)" ;; *) row FAIL "boot: firmware_class.path=/usr/lib/firmware/iceland-gpu-stock not among the managed options" ;; esac
	[ -e "$MNT/boot/iceland-managed-options" ] && row FAIL "boot: /boot/iceland-managed-options left in the image"
	grep -q "^devicetree /dtb-$KV/qcom/kaanapali-oneplus-iceland.dtb" "$e" && [ -e "$MNT/boot/dtb-$KV/qcom/kaanapali-oneplus-iceland.dtb" ] && row PASS "boot: per-kernel devicetree" || row FAIL "boot: devicetree line / file"
else row FAIL "boot: no entry for $KV"; fi
grep -q '^GRUB_DEVICETREE="qcom/kaanapali-oneplus-iceland.dtb"' "$MNT/etc/default/grub" && row PASS "boot: GRUB_DEVICETREE" || row FAIL "boot: GRUB_DEVICETREE"
grep -q '^menu_auto_hide=' "$MNT/boot/grub2/grubenv" 2>/dev/null && row FAIL "boot: grubenv menu_auto_hide set" || row PASS "boot: menu shown (no menu_auto_hide)"
( cd "$MNT/boot/efi" && find . -type f | sort ) > "$OUT/esp-files.txt"
for f in EFI/BOOT/BOOTAA64.EFI EFI/fedora/shimaa64.efi EFI/fedora/grubaa64.efi EFI/fedora/grub.cfg dtb/qcom/kaanapali-oneplus-iceland.dtb; do
	grep -qix "./$f" "$OUT/esp-files.txt" && row PASS "esp: $f" || row FAIL "esp: $f missing"
done
grep -qi "search.*--fs-uuid.*$(blkid -o value -s UUID "$P2")" "$MNT/boot/efi/EFI/fedora/grub.cfg" 2>/dev/null && row PASS "esp: grub.cfg stub finds /boot by UUID" || row FAIL "esp: grub.cfg stub does not point at /boot's UUID"
# ---- initramfs (the B run's "initramfs has" line, same patterns)
i=$MNT/boot/initramfs-$KV.img
if [ -s "$i" ] && command -v lsinitrd > /dev/null; then
	lsinitrd "$i" > "$OUT/lsinitrd.txt" 2>&1
	l=$OUT/lsinitrd.txt
	c=$(grep -c iceland-carrier "$l"); n=$(grep -c '/nbd.ko' "$l"); s=$(grep -c 59-iceland-storage-ro "$l"); z=$(grep -c gen80200_zap "$l")
	rf=$(grep -c -E '/(qcom_q6v5_adsp|qcom_q6v5_mss|ath1[0-2]k[^/]*|qcom-iris|venus-[a-z]*|btqca|hci_uart)\.ko' "$l")
	ed=$(grep -c -E '/qcom_q6v5_pas\.ko|kaanapali/iceland/(adsp|cdsp)(_dtb)?\.mbn' "$l")
	line="iceland-carrier $c nbd.ko $n storage rule $s zap $z root-firmware drivers $rf early dsp $ed; $(du -m "$i" | cut -f1) MiB"
	[ "$c" -ge 1 ] && [ "$n" = 1 ] && [ "$s" = 1 ] && [ "$z" = 1 ] && [ "$rf" = 0 ] && [ "$ed" = 5 ] && row PASS "initramfs: $line" || row FAIL "initramfs: $line (B149: carrier 3 nbd 1 rule 1 zap 1 root-firmware 0 early dsp 5)"
	g=$(grep -c -E 'usr/lib/firmware/iceland-gpu-stock/qcom/gen80200_(gmu\.bin|sqe\.fw)$' "$l")
	[ "$g" = 2 ] && row PASS "initramfs: stock's GPU pair (iceland-gpu-stock gmu + sqe)" || row FAIL "initramfs: stock's GPU pair $g of 2"
else row FAIL "initramfs: $i missing or no lsinitrd on the build host"; fi
# ---- manifest vs B149
rpm --root "$MNT" -qa --qf '%{NAME}\t%{EPOCHNUM}:%{VERSION}-%{RELEASE}\t%{ARCH}\n' | sort > "$OUT/manifest.tsv"
if [ -n "$REF" ]; then
	python3 -I "$HERE/manifest-diff.py" "$OUT/manifest.tsv" "$REF" --ours "$OURS" ${ALLOW:+--allow "$ALLOW"} > "$OUT/manifest-diff.txt" 2>&1
	md=$(tail -n 1 "$OUT/manifest-diff.txt"); case "$md" in *": PASS"*) row PASS "$md" ;; *) row FAIL "$md" ;; esac
else row PASS "manifest: $(wc -l < "$OUT/manifest.tsv") packages (no B149 reference given: not compared)"; fi
echo "IMAGE-CHECK: $([ "$nf" = 0 ] && echo PASS || echo FAIL) ($nf FAIL)" >> "$R"
cat "$R"
[ "$nf" = 0 ]
